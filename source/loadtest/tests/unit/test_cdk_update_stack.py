import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_update.cdk_update_stack import CdkUpdateStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_update/cdk_update_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkUpdateStack(app, "cdk-update")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
