import logging
import paramiko
import time

import boto.ec2


USERNAME = "ubuntu"
KEY_FILENAME = "/home/ubuntu/.ssh/sbr-01.pem"


logger = logging.getLogger(__name__)


class DaskPool:
    def __init__(
            self,
            region_name="us-east-1",
            image_id="ami-0dc8ed438643bfda3",
            target_count=3,
            key_name="dask-01",
            security_groups=["dask-01"],
            instance_type="t2.micro",
            max_sleep=60,
            branch="rl/distributed-script-processing",
            **kwargs
    ):
        self.region_name = region_name
        self.image_id = image_id
        self.target_count = target_count
        self.key_name = key_name
        self.security_groups = security_groups
        self.instance_type = instance_type
        self.max_sleep = max_sleep
        self.branch = branch
        self.connection = boto.ec2.connect_to_region(self.region_name, **kwargs)
        self.instances = []

    def maintain_pool(self):
        self.instances = self._get_instances()
        current_count = len(self.instances)
        logger.info("Current count: {0}".format(current_count))
        if current_count < self.target_count:
            self.add_to_pool(self.target_count - current_count)
        elif current_count > self.target_count:
            self.remove_from_pool(current_count - self.target_count)
        self._wait_for_pool(self.target_count)

    def add_to_pool(self, count):
        logger.info("Add count: {0}".format(count))
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
        logger.info("Remove count: {0}".format(count))
        self.instances = self._get_instances()
        instance_ids = []
        for i in self.instances:
            instance_ids.append(i.id)
            if len(instance_ids) == count:
                break
        self.connection.stop_instances(instance_ids)
        self._wait_for_pool(len(self.instances) - count)

    def terminate_pool(self):
        self.instances = self._get_instances()
        for i in self.instances:
            logger.info("Terminating instance: {0}".format(i.id))
            i.terminate()
        self._wait_for_pool(0)

    def restart_pool(self):
        self.terminate_pool()
        self.maintain_pool()

    def checkout_branch(self):
        commands = " ; ".join(
            [
                "cd secure-bioinformatics-reuse",
                "git stash",
                "git checkout " + self.branch,
                "git pull",
            ]
        )
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # client.load_system_host_keys()
        for i in self.instances:
            logger.info("Updating instance: {0}".format(i.id))
            client.connect(
                i.ip_address,
                username=USERNAME,
                key_filename=KEY_FILENAME,
            )
            f_stdin, f_stdout, f_stderr = client.exec_command(commands)
            exit_code = f_stdout.channel.recv_exit_status()
            stdout = f_stdout.read()
            stderr = f_stderr.read()
            if exit_code != 0:
                raise Exception(stderr)
            else:
                logger.debug(stdout)
            client.close()

    def _get_instances(self):
        instances = []
        reservations = self.connection.get_all_reservations()
        for r in reservations:
            for i in r.instances:
                if (i.image_id == self.image_id
                    and i.instance_type == self.instance_type
                    and i.state == "running"):
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
