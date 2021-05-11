import time

import boto.ec2


class DaskPool:
    def __init__(
        self,
        region_name="us-east-1",
        image_id="ami-0c753a2f9c97b67a5",
        target_count=3,
        key_name="dask-0.1.0",
        security_groups=["dask-0.1.0"],
        instance_type="t2.micro",
        max_sleep=60,
        **kwargs
    ):
        self.region_name = region_name
        self.image_id = image_id
        self.target_count = target_count
        self.key_name = key_name
        self.security_groups = security_groups
        self.instance_type = instance_type
        self.max_sleep = max_sleep
        self.connection = boto.ec2.connect_to_region(self.region_name, **kwargs)
        self.instances = []

    def maintain_pool(self):
        self.instances = self._get_instances()
        current_count = len(self.instances)
        if current_count < self.target_count:
            self.add_to_pool(self.target_count - current_count)
        elif current_count > self.target_count:
            self.remove_from_pool(current_count - self.target_count)
        self._wait_for_pool(self.target_count)

    def add_to_pool(self, count):
        self.instances = self._get_instances()
        self.connection.run_instances(
            self.image_id,
            min_count=count,
            max_count=count,
            key_name=self.key_name,
            security_groups=self.security_groups,
            instance_type=self.instance_type,
        )
        self._wait_for_pool(len(self.instances) + count)

    def remove_from_pool(self, count):
        self.instances = self._get_instances()
        instance_ids = []
        for i in self.instances:
            instance_ids.append(i.id)
            if len(instance_ids) == count:
                break
        self.connection.stop_instances(instance_ids)
        self._wait_for_pool(len(self.instances) - count)

    def restart_pool(self):
        self.terminate_pool()
        self.maintain_pool()

    def terminate_pool(self):
        self.instances = self._get_instances()
        for i in self.instances:
            i.terminate()
        self._wait_for_pool(0)

    def _get_instances(self):
        instances = []
        reservations = self.connection.get_all_reservations()
        for r in reservations:
            for i in r.instances:
                if i.image_id == self.image_id and i.state == "running":
                    instances.append(i)
        return instances

    def _wait_for_pool(self, count):
        sleep = 0
        while sleep < self.max_sleep:
            self.instances = self._get_instances()
            if len(self.instances) == count:
                break
            else:
                time.sleep(1)
                sleep += 1


def main():
    pass


if __name__ == "__main__":
    main()
