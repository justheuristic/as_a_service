import threading
import sys
import time
from concurrent.futures import Future

if sys.version_info >= (3, 0):
    import queue
else:
    import Queue as queue


class BatchedService(threading.Thread):
    NO_MORE_ITEMS = 0xDEADC0DE

    def __init__(self, batch_process_func, batch_size, max_delay, max_queued=0, start=True):
        """
        Turns a function into a thread that groups function calls into batches and processes them together.

        Batches are processed either if they contain batch_size elements or
        if max_delay time has passed since the first unprocessed request in batch

        :param batch_process_func: a function that takes a list of items and returns a list of results
        :param batch_size: maximum number of queries processed in one function run.
            Typically "as many as you can handle"
        :param max_delay: maximum amount of time [float, seconds] that service can
            wait for new requests to fill the batch.
            A batch is processed after max_delay even if it isn't full.
            if 0, don't wait at all (groups only items submitted since last run, but at most batch_size of them)
        :param max_queued: maximum number of elements that can be queued. 0(default) means unlimited

        Notes:
         - It's safe to change batch_size and max_delay on the fly, provided they are valid (e.g. not inf)
         -

        Example use case: a neural network on GPU that has to process a stream of requests.
        >>> my_network = make_keras_network_on_gpu()
        >>> service = BatchedService(my_network.predict, batch_size=32, max_delay=1.0, start=True)
        >>> for i in range(9000):
        >>>     start_thread_that_need_my_network(predict_one=lambda x: service(x))
        >>> service.stop()

        Doesn't use asyncio (works just the same in jupyter/script/py2.7/3.5/...).
        For asyncio version, see http://blog.mathieu-leplatre.info/some-python-3-asyncio-snippets.html
        """
        self.batch_process_func = batch_process_func
        self.batch_size = batch_size
        self.max_delay = max_delay
        self.queue = queue.Queue(max_queued)
        self.lock_closing = threading.Lock()
        self.closing = False
        super().__init__()
        if start: self.start()

    def run(self):
        while not self.closing:
            # gather batch
            futures, items, deadline = [], [], time.time() + self.max_delay
            try:
                for i in range(self.batch_size):
                    future, item = self.queue.get(timeout=deadline - time.time())
                    if future == self.NO_MORE_ITEMS: return
                    futures.append(future)
                    items.append(item)
            except queue.Empty:
                pass

            # process batch
            if len(items):
                for future, result in zip(futures, self.batch_process_func(items)):
                    future.set_result(result)

    def __call__(self, item, timeout=None):
        """ Submit item for processing, wait for it to process and return the result """
        return self.submit(item).result(timeout)

    def submit(self, item):
        """
        Submits an item for processing, returns Future for function output
        To get the actual output, call .result() on future.
        """
        assert not self.closing, "Service is closing, no new requests can be submitted"
        future = Future()
        self.queue.put((future, item))
        return future

    def submit_many(self, items):
        """
        Convenience function: submit multiple items to a queue, return a list of Future-s for each item.
        If service was not ordered to stop yet, it won't be until all items are submitted.
        """
        with self.lock_closing:
            return [self.submit(item) for item in items]

    def join(self, timeout=None):
        raise ValueError("Please use .stop(...) instead of .join")

    def stop(self, wait=True, timeout=None, hard=False):
        """
        Process all unfinished jobs and stop the thread.
        :param wait: if True, waits for the thread to join before returning
        :param timeout: maximum time waiting if wait==True
        :param hard: if True, does not process unfinished jobs from query (leaving them hanging)
        """
        with self.lock_closing:
            self.closing = True
        if hard:
            while not self.queue.empty():
                self.queue.get_nowait()
        self.queue.put((self.NO_MORE_ITEMS, None))
        if wait:
            return threading.Thread.join(self, timeout)


def as_batched_service(batch_size, max_delay, max_queued=0, start=True):
    """
    decorator version of BatchedService. See BatchedService itself for docs
    Example:
    >>> @as_batched_service(batch_size=3, max_delay=0.1)
    >>> def square(batch_xs):
    >>>     print("processing...", batch_xs)
    >>>     return [x_i ** 2 for x_i in batch_xs]
    >>> futures = square.submit_many(range(10))
    >>> print([f.result() for f in futures])
    """
    def wrap(batch_process_func):
        service = BatchedService(batch_process_func, batch_size, max_delay,
                                 max_queued=max_queued, start=start)
        return service
    return wrap


def as_service(max_delay=1.0, max_queued=0, start=True):
    """
    turns a function(x) -> f(x) into a thread-safe "service" that
    - is capable of asynchronous processing via .submit()
    - processes one request at a time no matter how many threads call it simultaneously
    - processes requests in the order they were submitted

    This is useful to avoid errors when interacting with files/network/external_stuff.
    Example:
    >>> @as_service()
    >>> def write_read(value):
    >>>     os.system('echo {} > tmp.txt'.format(value)) # this function should not be run concurrently
    >>>     time.sleep(1.0)
    >>>     output = open('tmp.txt').read()
    >>>     os.remove("tmp.txt")
    >>>     return output
    >>> tasks = [joblib.delayed(write_read, check_pickle=False)(x) for x in range(5)]
    >>> joblib.Parallel(n_jobs=5, backend='threading')(tasks)
    """
    def wrap(item_process_func):
        def _process(items):
            assert len(items) == 1, "expected 1 element in batch, got %i" % len(items)
            return [item_process_func(items[0])]
        service = BatchedService(_process, batch_size=1, max_delay=max_delay,
                                 max_queued=max_queued, start=start)
        return service
    return wrap
