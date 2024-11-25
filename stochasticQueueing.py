
import simpy
import queue
import numpy.random as rand

class ServerQueueingSimulation:

    arrival_dist = None
    duration_dist = None
    server_count = 1
    server_busy = []
    q = queue.Queue()
    queue_type = ''
    max_queue_len = 1000
    job_count = 0

    env = None
    
    verbose = False

    def __init__(self, arrival_dist = None, duration_dist = None, server_count = 1, queue_type = 'FIFO', max_queue_len = 1000, seed = 42, verbose = False):
        
        
        self.verbose = verbose
        
        rand.seed(42)
        
        print('starting Simulation')

        self.server_count = server_count
        self.server_busy = [False for i in range(self.server_count)]

        
        if self.queue_type == 'FIFO':
            self.q = queue.Queue()

        if arrival_dist == None:
            self.arrival_dist = lambda : rand.exponential(0.5)
        else: 
            self.arrival_dist = arrival_dist


        if duration_dist == None:
            self.duration_dist = lambda : rand.exponential(1)
        else: 
            self.duration_dist = duration_dist




        self.env = simpy.Environment()
        self.env.process(self.job_arrival())
        self.env.run(until=150)

    



    def job_arrival(self):
        while True:

            if self.q.qsize() == self.max_queue_len:
                if self.verbose:
                    print("job_rejected")
                return
            self.q.put(self.job_count)
            self.job_count += 1
            self.update_queue()
            new_job_wait = self.arrival_dist()


            yield self.env.timeout(new_job_wait)



    def server_job(self, server_index):

        duration = self.duration_dist()
        self.server_busy[server_index] = True
        if self.verbose:
            print("{}: Server {} starting job".format(self.env.now, server_index))

        yield self.env.timeout(duration)
        if self.verbose:
            print("{}: Server {} finishing job".format(self.env.now, server_index))
        self.server_busy[server_index] = False
        self.update_queue()




    def update_queue(self):
        print(self.q.queue)
        if self.q.empty():
            return
        for i in range(self.server_count):
            if(not self.server_busy[i]):
                job = self.q.get()
                self.env.process(self.server_job(i))
                return

            
if __name__ == '__main__':
    ServerQueueingSimulation(server_count=2, verbose=True)
    