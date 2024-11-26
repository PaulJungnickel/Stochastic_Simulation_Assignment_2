import simpy
import queue
import numpy.random as rand
import numpy as np


class ServerQueueingSimulation:
    def __init__(
        self,
        arrival_rate=1.0,
        service_rate=1.0,
        server_count=1,
        queue_type='FIFO',
        max_queue_len=1000,
        sim_duration=150,
        seed = 42,
        verbose=False
    ):
        self.verbose = verbose
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.server_count = server_count
        self.max_queue_len = max_queue_len
        self.sim_duration = sim_duration
        self.job_count = 0
        self.rejected_jobs = 0
        self.total_waiting_time = 0
        self.completed_jobs = 0
        self.seed = seed

        rand.seed(self.seed)

        self.server_busy = [False for _ in range(self.server_count)]
        self.queue = queue.Queue() if queue_type == 'FIFO' else None

        self.env = simpy.Environment()
        self.env.process(self.job_arrival())
        self.env.run(until=self.sim_duration)

    def job_arrival(self):
        while True:
            if self.queue.qsize() >= self.max_queue_len:
                self.rejected_jobs += 1
                if self.verbose:
                    print(f"{self.env.now}: Job rejected.")
            else:
                self.queue.put((self.env.now, self.job_count))  # Add arrival time and job ID
                self.job_count += 1
                self.update_queue()

            yield self.env.timeout(rand.exponential(1 / self.arrival_rate))

    def server_job(self, server_index, arrival_time):
        self.server_busy[server_index] = True
        start_time = self.env.now
        wait_time = start_time - arrival_time
        self.total_waiting_time += wait_time
        if self.verbose:
            print(f"{start_time:.2f}: Server {server_index} starting job with wait time {wait_time:.2f}")

        yield self.env.timeout(rand.exponential(1 / self.service_rate))

        self.completed_jobs += 1
        self.server_busy[server_index] = False
        if self.verbose:
            print(f"{self.env.now:.2f}: Server {server_index} finished job.")
        self.update_queue()

    def update_queue(self):
        if self.queue.empty():
            return
        for i in range(self.server_count):
            if not self.server_busy[i] and not self.queue.empty():
                arrival_time, job_id = self.queue.get()
                self.env.process(self.server_job(i, arrival_time))

    def results(self):
        avg_wait_time = self.total_waiting_time / self.completed_jobs if self.completed_jobs > 0 else float('inf')
        rejection_rate = self.rejected_jobs / self.job_count if self.job_count > 0 else 0
        return {
            "Average Wait Time": avg_wait_time,
            "Rejection Rate": rejection_rate,
            "Completed Jobs": self.completed_jobs,
            "Total Jobs": self.job_count,
            "Rejected Jobs": self.rejected_jobs,
        }


if __name__ == '__main__':
    arrival_rate = 5.0  # λ
    service_rate = 6.0  # μ
    sim_duration = 150
    num_runs = 50  
    server_counts = [1, 2, 4]

    for n in server_counts:
        results = []
        for run_number in range(num_runs):
            sim = ServerQueueingSimulation(
                arrival_rate=arrival_rate,
                service_rate=service_rate,
                server_count=n,
                sim_duration=sim_duration,
                seed = run_number,
                verbose=False,
            )
            results.append(sim.results()["Average Wait Time"])

        mean_wait_time = np.mean(results)
        std_dev = np.std(results, ddof=1)
        print(f"n = {n}, Mean Wait Time = {mean_wait_time:.4f}, Std Dev = {std_dev:.4f}")
