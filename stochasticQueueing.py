
import simpy
import queue
import numpy.random as rand

class ServerQueueingSimulation:

    arrival_dist = None
    duration_dist = None
    server_count = 1
    server_busy = []
    q = None
    queue_type = 'FIFO'
    max_queue_len = 100
    job_count = 0

    env = None

    def __init__(self):
        print('starting Simulation')


        self.server_busy = [False for i in range(self.server_count)]

        
        if self.queue_type == 'FIFO':
            self.q = queue.Queue()

        if self.arrival_dist == None:
            self.arrival_dist = rand.exponential


        if self.duration_dist == None:
            self.duration_dist = rand.exponential




        self.env = simpy.Environment()
        self.env.process(self.job_arrival())
        self.env.run(until=15)

    



    def job_arrival(self):
        while True:

            if self.q.qsize() == self.max_queue_len:
                print("job_rejected")
                return
            self.q.put(self.job_count)
            self.update_queue()
            new_job_wait = self.arrival_dist()


            yield self.env.timeout(new_job_wait)



    def server_job(self, server_index):

        duration = self.duration_dist()
        self.server_busy[server_index] = True
        print("{}: Server {} starting job".format(self.env.now, server_index))

        yield self.env.timeout(duration)

        print("{}: Server {} finishing job".format(self.env.now, server_index))
        self.server_busy[server_index] = False
        self.update_queue()




    def update_queue(self):
        if self.q.empty():
            return
        for i in range(self.server_count):
            if(not self.server_busy[i]):
                job = self.q.get()
                self.env.process(self.server_job(i))
                return

            
if __name__ == '__main__':
    ServerQueueingSimulation()
