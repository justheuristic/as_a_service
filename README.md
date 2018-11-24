# batched_service

A simple package that transforms a batch function {inputs->results} into a service that
- groups inputs into batches - you specify max batch size and time waiting
- processes them - and returns results back to whoever was asking

### Install:
 *  ```pip install as_a_service```
 *  No dependencies apart from standard libraries
 *  Works with both python2 and python3 (pip3 install)


### Usage:

Here's how it feels
```
@as_batched_service(batch_size=3, max_delay=0.1)
def square(batch_xs):
    print("processing...", batch_xs)
    return [x_i ** 2 for x_i in batch_xs]

# submit many queries
futures = square.submit_many(range(10))
print([f.result() for f in futures])
```
This will print
```
processing... [0, 1, 2]
processing... [3, 4, 5]
processing... [6, 7, 8]
processing... [9]
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
```

You can also use it as a drop-in replacement for a function that processes one input at a time
 * `square(2.0)` will return 4.0 as if a normal function
 * Under the hood, it submits a request and waits for it to finish

This package contains three objects
 - BatchedService(batch_process_func, batch_size, max_delay) - main object
 - @as_batched_service(batch_size, max_delay) - decorator version
 - @as_service(max_delay) - decorator for service without batches

Use help(BatchedService) for details.


### Why should I care?

This primitive is useful for a number of scenarios like:
1) You are building a web-based demo around your neural network. You want your network to process
    a stream of user queries, but doing so one query at a time is slow. Batch-parallel processing is way better.

```
@as_batched_service(batch_size=32, max_delay=1.0)
def service_predict(input_images_list):
    predictions_list = my_network_predict_batch(input_images_list)
    return predictions_list

@my_web_framework.run_as_a_thread_for_every_query
def handle_user_query(query):
    input_image = get_image(query)
    return service_predict(input_image)
```

2) You are experimenting with a reinforcement learning agent. The agent itself is a neural network
    that predicts actions. You want to play 100 parallel game sessions to train on.
    Playing one session at a time is slow. If only we could run multiple sessions on one GPU

```
my_network = make_keras_network_on_gpu()
service = BatchedService(my_network.predict, batch_size=32, max_delay=1.0)
threads = [
    GamePlayingThread(predict_action=lambda x: service(x)) for i in range(100)
]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()
service.stop()
```

And many other scenarios where you want to use a single resource
(GPU / device /DB) concurrently and utilize batch-parallelism
