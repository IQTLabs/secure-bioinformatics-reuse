from dask.distributed import Client, SSHCluster

from DaskPool import DaskPool


def inc(x):
    return x + 1


def add(x, y):
    return x + y


def main():
    daskPool = DaskPool()
    daskPool.maintain_pool()
    cluster = SSHCluster(
        [i.ip_address for i in daskPool.instances],
        connect_options={"known_hosts": None, "client_keys": ['~/.ssh/dask-01.pem']},
        worker_options={"nthreads": 2},
        scheduler_options={"port": 0, "dashboard_address": ":8797"}
    )
    client = Client(cluster)
    a = client.submit(inc, 1)
    b = client.submit(inc, 2)
    c = client.submit(add, a, b)
    c = c.result()
    print(c)


if __name__ == "__main__":
    main()
