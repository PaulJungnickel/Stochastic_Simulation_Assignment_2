import simpy
import queue
import numpy.random as rand
import numpy as np


class ServerQueueingSimulation:
    def __init__(
        self,
        arrival_dist,
        service_dist,
        server_count=1,
        queue_type='FIFO',
        max_queue_len=1000,
        sim_duration=150,
        warmup_duration=0,
        seed=42,
        verbose=False,
    ):
        """
        Initializes the server queueing simulation with given parameters.

        Parameters:
        - arrival_dist: Generator function with distribution of job arrivals.
        - service_dist: Generator function with distribution of job service durations.
        - server_count: Number of servers available (default: 1).
        - queue_type: 'FIFO' or 'SJF' (default: 'FIFO').
        - max_queue_len: Maximum length of the queue before rejecting jobs (default: 1000).
        - sim_duration: Total duration of the simulation (default: 150).
        - warmup_duration: Time to run the simulation before starting to compute statistics
        - seed: Random seed for reproducibility (default: 42).
        - service_dist: Service time distribution type ('exponential', 'deterministic', 'hyperexponential').
        - verbose: Whether to print detailed output during the simulation (default: False).
        """
        self.verbose = verbose
        self.arrival_dist = arrival_dist
        self.service_dist = service_dist
        self.server_count = server_count
        self.max_queue_len = max_queue_len
        self.sim_duration = sim_duration
        self.warmup_duration = warmup_duration
        assert warmup_duration < sim_duration
        self.job_count = 0
        self.rejected_jobs = 0
        self.total_waiting_time = 0
        self.completed_jobs = 0
        self.seed = seed

        # Set the random seed for reproducibility
        rand.seed(self.seed)

        # Initialize server states (all servers start as not busy) and the queue
        self.server_busy = [False for _ in range(self.server_count)]
        if queue_type == 'FIFO':
            self.queue = queue.Queue()
        elif queue_type == 'SJF':
            self.queue = queue.PriorityQueue()
        else:
            raise ValueError("Unsupported queue type. Use 'FIFO' or 'SJF'.")

        # Create the SimPy environment and start the job arrival process
        self.env = simpy.Environment()
        self.env.process(self.job_arrival())
        self.env.process(self.end_of_warmup(self.warmup_duration))
        self.env.run(until=self.sim_duration)

    def job_arrival(self):
        """
        Simulates the arrival of jobs at random intervals based on the specified arrival rate.
        If the queue is full, jobs are rejected.
        """
        while True:
            # Check if the queue has reached maximum capacity
            if self.queue.qsize() >= self.max_queue_len:
                self.rejected_jobs += 1
                if self.verbose:
                    print(f"{self.env.now}: Job rejected.")
            else:
                # Generate a job with an arrival time and a service duration
                arrival_time = self.env.now
                service_time = self.service_dist()
                job = (service_time, self.job_count, arrival_time)  # For SJF: use service_time as priority
                self.queue.put(job)
                self.job_count += 1
                # Attempt to assign a job to an idle server
                self.update_queue()

            # Wait for the next job arrival, based on an exponential distribution
            yield self.env.timeout(self.arrival_dist())

    def server_job(self, server_index, job):
        """
        Processes a job by a server.

        Parameters:
        - server_index: Index of the server that processes the job.
        - job: A tuple containing service time, job ID, and arrival time.
        """
        # Unpack the job details
        service_time, job_id, arrival_time = job
        start_time = self.env.now
        wait_time = start_time - arrival_time
        self.total_waiting_time += wait_time
        if self.verbose:
            print(f"{start_time:.2f}: Server {server_index} starting job {job_id} with wait time {wait_time:.2f}")

        # Process the job
        self.server_busy[server_index] = True
        yield self.env.timeout(service_time)

        # Job completion
        self.completed_jobs += 1
        self.server_busy[server_index] = False
        if self.verbose:
            print(f"{self.env.now:.2f}: Server {server_index} finished job {job_id}.")
        self.update_queue()

    def update_queue(self):
        """
        Assigns jobs from the queue to available servers if any are idle.
        """

        if self.queue.empty():
            return
        
        # Iterate over each server and assign available jobs to idle servers
        for i in range(self.server_count):
            if not self.server_busy[i] and not self.queue.empty():
                # SJF
                if isinstance(self.queue, queue.PriorityQueue): 
                    job = self.queue.get_nowait()
                # FIFO
                else:  
                    job = self.queue.get_nowait()
                self.env.process(self.server_job(i, job))


    def end_of_warmup(self, warmup_duration):
        """
        Resets the counting statistics at the end of the warmup period
        """        
        yield self.env.timeout(warmup_duration)
        self.job_count = 0
        self.rejected_jobs = 0
        self.total_waiting_time = 0
        self.completed_jobs = 0


    def results(self):
        """
        Returns the results of the simulation.

        Returns:
        - Dictionary with average wait time, rejection rate, completed jobs, total jobs, and rejected jobs.
        """        
        while not self.queue.empty():
            job = self.queue.get()
            arrival_time = job[2]

            self.total_waiting_time += self.sim_duration - arrival_time
            
        avg_wait_time = self.total_waiting_time / self.job_count if self.job_count > 0 else float('inf')
        rejection_rate = self.rejected_jobs / self.job_count if self.job_count > 0 else 0
        return {
            "Average Wait Time": avg_wait_time,
            "Rejection Rate": rejection_rate,
            "Completed Jobs": self.completed_jobs,
            "Total Jobs": self.job_count,
            "Rejected Jobs": self.rejected_jobs,
        }



if __name__ == '__main__':
    # some code for 2.3
    import matplotlib.pyplot as plt


    def M_M_n_simulation(system_load, server_count, sim_duration, seed=42, queue_type='FIFO'):
        arrival_rate = server_count
        service_rate = 1 / system_load

        arrival_dist = lambda: rand.exponential(1 / arrival_rate)
        service_dist = lambda: rand.exponential(1 / service_rate)

        sim = ServerQueueingSimulation(
            arrival_dist, service_dist, server_count, queue_type=queue_type, sim_duration=sim_duration, seed=seed
        )
        return sim.results()

    server_counts = [1]
    num_runs = 50
    rand.seed(42)
    system_loads = 1 - np.logspace(-0.5, -7, 15)

    for queue_type in ['FIFO', 'SJF']:
        for server_count in server_counts:
            mean_wait_time = np.zeros_like(system_loads)
            std_wait_time = np.zeros_like(system_loads)
            for i, system_load in enumerate(system_loads):
                wait_times = np.zeros(num_runs)
                for j in range(num_runs):
                    res = M_M_n_simulation(
                        system_load, server_count, 1000, seed=rand.randint(0, 2**31 - 1), queue_type=queue_type
                    )
                    wait_times[j] = res['Average Wait Time']

                mean_wait_time[i] = np.mean(wait_times)
                std_wait_time[i] = np.std(wait_times)
            plt.errorbar(
                1 - system_loads,
                mean_wait_time,
                std_wait_time,
                linestyle='',
                label=f'{queue_type}, n={server_count}',
                capsize=5,
                elinewidth=1,
            )

    plt.grid()
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel(r'$1-\rho$')
    plt.ylabel('mean wait time')
    plt.legend(title='Queue Type and Server Count')
    plt.show()
