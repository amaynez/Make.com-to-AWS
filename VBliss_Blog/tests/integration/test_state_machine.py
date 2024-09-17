import logging
import os
from time import sleep
from typing import Dict
from unittest import TestCase
from uuid import uuid4

import boto3
from botocore.client import BaseClient

"""
Make sure env variable AWS_SAM_STACK_NAME exists with the name of the stack we are going to test. 
"""


class TestStateMachine(TestCase):
    """
    This integration test will execute the step function and verify
    - "Record Transaction" is executed
    - the record has been inserted into the transaction record table.
    * The inserted record will be removed when test completed.
    """

    state_machine_arn: str
    transaction_table_name: str

    client: BaseClient
    inserted_record_id: str

    @classmethod
    def get_and_verify_stack_name(cls) -> str:
        stack_name = os.environ.get("AWS_SAM_STACK_NAME")
        if not stack_name:
            raise Exception(
                "Cannot find env var AWS_SAM_STACK_NAME. \n"
                "Please setup this environment variable with the stack name where we are running integration tests."
            )

        # Verify stack exists
        client = boto3.client("cloudformation")
        try:
            client.describe_stacks(StackName=stack_name)
        except Exception as e:
            raise Exception(
                f"Cannot find stack {stack_name}. \n" f'Please make sure stack with the name "{stack_name}" exists.'
            ) from e

        return stack_name

    @classmethod
    def setUpClass(cls) -> None:
        """
        Based on the provided env variable AWS_SAM_STACK_NAME,
        here we use cloudformation API to find out:
        - StockTradingStateMachine's ARN
        - TransactionTable's table name
        """
        stack_name = TestStateMachine.get_and_verify_stack_name()

        client = boto3.client("cloudformation")
        response = client.list_stack_resources(StackName=stack_name)
        resources = response["StackResourceSummaries"]
        state_machine_resources = [
            resource for resource in resources if resource["LogicalResourceId"] == "VBlissBlogStateMachine"
        ]
        if not state_machine_resources:
            raise Exception("Cannot find VBlissBlogStateMachine")

        cls.state_machine_arn = state_machine_resources[0]["PhysicalResourceId"]

    def setUp(self) -> None:
        self.client = boto3.client("stepfunctions")

    def _start_execute(self) -> str:
        """
        Start the state machine execution request and record the execution ARN
        """
        response = self.client.start_execution(
            stateMachineArn=self.state_machine_arn, name=f"integ-test-{uuid4()}", input="{}"
        )
        return response["executionArn"]

    def _wait_execution(self, execution_arn: str):
        while True:
            response = self.client.describe_execution(executionArn=execution_arn)
            status = response["status"]
            if status == "SUCCEEDED":
                logging.info(f"Execution {execution_arn} completely successfully.")
                break
            elif status == "RUNNING":
                logging.info(f"Execution {execution_arn} is still running, waiting")
                sleep(3)
            else:
                self.fail(f"Execution {execution_arn} failed with status {status}")

    def test_state_machine(self):
        execution_arn = self._start_execute()
        self._wait_execution(execution_arn)
