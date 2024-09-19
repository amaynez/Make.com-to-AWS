# Make.com-to-AWS

This is an experiment to try to recreate a complex [Make.com](https://make.com) scenario using AWS Step Functions

I have a business and this business has a blog, I got the idea of using LLMs to write SEO relevant blog posts. I discovered [Make.com](https://make.com) and in no time I was fully automated. I purchased the 10,000 operations a month plan, and it always runs out by day 20 of the month, because I also have other automations like creating LinkedIn posts on my personal page, doing some sync on some database backups between airtable, notion and Google sheets, and some deduplications. It is a fantastic tool, and I love it. Specially because I can do quite complex things with it very quickly. I now want to increase the frequency of the blog posts scenario but that would mean that I have to purchase a larger plan, even after optimizing all my scenarios for minimal operations (for instance the blog post one originally used up 230 operations per run, and now it only uses 57). So I did the math and it turns out that using AWS Step Functions and some Lambdas I can have the same functionality but much cheaper (if you compare the spend per operation). Obviously at the great cost of taking much longer to program everything. For instance parsing JSON which is just a piece of cake in [Make.com](https://make.com), is a pain when coding it yourself. Im between jobs at the moment so I am taking this opportunity to learn how Step Functions work in AWS by recreating my Make.com scenarios. I will then run them for a month and see if it is truly cheaper or not. But in the mean time at least I spent some time sharpening my python skills and learning some cloud development which is completely new to me. This is the repo for this. I think that for use cases like mine where I don’t need to change or create scenarios constantly, but have a more stable automation landscape, it make sense to go from no-code to code. Otherwise, [Make.com](https://make.com) is brilliant to create scenarios quite quickly. Let me know if it makes sense to you.

The scenarios I redid as applications are:

1. [VBliss Blog](https://github.com/amaynez/Make.com-to-AWS/tree/main/VBliss_Blog)

[Original Reddit Post](https://www.reddit.com/r/Integromat/comments/1fh5qzv/user_of_makecom_started_to_migrate_scenarios_to/)

## How to use

Each application contains:

- functions - Code for the application's Lambda functions to check the value of, buy, or sell shares of a stock.
- statemachines - Definition for the state machine that orchestrates the stock trading workflow.
- template.yaml - A template that defines the application's AWS resources.

Each application uses several AWS resources, including Step Functions state machines, Lambda functions and an EventBridge rule trigger. These resources are defined in the `template.yaml` file in each project. You can update the template to add AWS resources through the same deployment process that updates your application code.

If you prefer to use an integrated development environment (IDE) to build and test the Lambda functions within your application, you can use the AWS Toolkit. The AWS Toolkit is an open source plug-in for popular IDEs that uses the SAM CLI to build and deploy serverless applications on AWS. The AWS Toolkit also adds a simplified step-through debugging experience for Lambda function code. See the following links to get started:

* [CLion](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [GoLand](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [IntelliJ](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [WebStorm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [Rider](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [PhpStorm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [PyCharm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [RubyMine](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [DataGrip](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [VS Code](https://docs.aws.amazon.com/toolkit-for-vscode/latest/userguide/welcome.html)
* [Visual Studio](https://docs.aws.amazon.com/toolkit-for-visual-studio/latest/user-guide/welcome.html)

The AWS Toolkit for VS Code includes full support for state machine visualization, enabling you to visualize your state machine in real time as you build. The AWS Toolkit for VS Code includes a language server for Amazon States Language, which lints your state machine definition to highlight common errors, provides auto-complete support, and code snippets for each state, enabling you to build state machines faster.

### Prerequisites

Here are the steps to create a local development environment in VS Code on a Mac to develop and deploy Python Lambda functions to AWS:

## 1. Install Prerequisites

[Python 3 installed](https://www.python.org/downloads/)
<details>
<summary>Install AWS CLI:</summary>

<details>
<summary>Step 1: Download the AWS CLI installer</summary>

**For Windows:**

1. Go to the official [AWS CLI download page:](https://awscli.amazonaws.com/AWSCLIV2.msi)
2. Click on the link to download the MSI installer for Windows.

**For macOS:**

1. Download the [macOS PKG installer:](https://awscli.amazonaws.com/AWSCLIV2.pkg)

**For Linux:**

1. Download the Linux installer:

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
```

</details>

<details>
<summary>Step 2: Run the installer</summary>

**For Windows:**

1. Locate the downloaded MSI file (usually in your Downloads folder).
2. Double-click the file to run the installer.
3. Follow the on-screen instructions to complete the installation.

**For macOS:**

1. Locate the downloaded PKG file.
2. Double-click the file to run the installer.
3. Follow the on-screen instructions to complete the installation.

**For Linux:**
Run the following command:

```bash
sudo ./aws/install
```

</details>

<details>
<summary>Step 3: Verify the installation</summary>

For all platforms (Windows, macOS, Linux):

1. Open a new command prompt, terminal, or shell.
2. Type the following command and press Enter:

```bash
aws --version
```

3. You should see output similar to this:

```bash
aws-cli/2.17.20 Python/3.11.6 Windows/10 exe/AMD64 prompt/off
```

This confirms that AWS CLI is installed correctly.

</details>

<details>
<summary>Step 4: Configure AWS CLI</summary>

For all platforms (Windows, macOS, Linux):

1. Open a command prompt, terminal, or shell.
2. Run the following command:

```bash
aws configure
```

3. You'll be prompted to enter the following information:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region name (e.g., us-west-2)
   - Default output format (e.g., json)

4. Enter your credentials and preferences when prompted.

</details>

<details>
<summary>Step 5: Test the AWS CLI</summary>

For all platforms (Windows, macOS, Linux):

To ensure AWS CLI is working correctly, try a simple command:

```bash
aws s3 ls
```

This will list all S3 buckets in your account if configured correctly.

</details>

By following these steps, you should have AWS CLI installed and configured on your Windows, macOS, or Linux system. Remember to keep your AWS CLI updated for the latest features and security improvements.

</details>
[Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)
<details>
<summary> Install SAM CLI </summary>
Here's a step-by-step guide on how to install AWS SAM CLI on Windows, macOS, and Linux:

[Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)

### Prerequisites for the SAM CLI

Before installing AWS SAM CLI, ensure you have:

1. An AWS account
2. AWS CLI installed and configured
3. Appropriate permissions to create and manage AWS resources

### Windows Installation

1. **Download the installer**:
   - Go to the [AWS SAM CLI releases page](https://github.com/aws/aws-sam-cli/releases/latest)
   - Download the Windows installer (MSI file)

2. **Run the installer**:
   - Double-click the downloaded MSI file
   - Follow the on-screen instructions

3. **Verify the installation**:
   - Open a new command prompt
   - Run: `sam --version`

4. **Enable long paths** (Windows 10 and newer):
   - Open the Group Policy Editor
   - Navigate to Computer Configuration > Administrative Templates > System > Filesystem
   - Enable "Enable Win32 long paths"

5. **Install Git** (if not already installed):
   - Download and install Git from [git-scm.com](https://git-scm.com/)

### macOS Installation

1. **Install Homebrew** (if not already installed):

   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
   ```

2. **Install AWS SAM CLI**:

   ```bash
   brew tap aws/tap
   brew install aws-sam-cli
   ```

3. **Verify the installation**:

   ```bash
   sam --version
   ```

### Linux Installation

1. **Download the AWS SAM CLI package**:

   ```bash
   curl -L "https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip" -o "aws-sam-cli-linux-x86_64.zip"
   ```

2. **Unzip the package**:

   ```bash
   unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
   ```

3. **Install AWS SAM CLI**:

   ```bash
   sudo ./sam-installation/install
   ```

4. **Verify the installation**:

   ```bash
   sam --version
   ```

### Post-Installation Steps

After installing AWS SAM CLI on any platform:

1. **Configure AWS credentials** (if not already done):

   ```bash
   aws configure
   ```

2. **Test SAM CLI**:

   ```bash
   sam init
   ```

This will start a guided process to create a sample serverless application.

By following these steps, you should have AWS SAM CLI successfully installed on your Windows, macOS, or Linux machine.

</details>

## 2. Setup Python Environment in VS Code or your favorite IDE

* Install the Python extension in VS Code
* Open a new workspace folder for your project
* Select the Python interpreter to use

## 3. Create a New SAM Application

* Open the Command Palette (Shift+Command+P)
* Select **AWS: Create new SAM Application**
* Choose Python as the runtime
* Provide an application name

This will generate boilerplate code for a Python Lambda function.

## 4. Clone this repository where your SAM Application is

## 5. Deploy the solution

* Build and deploy your application:

```bash
sam build --use-container
sam deploy --guided
```

The SAM CLI installs dependencies defined in `functions/*/requirements.txt`, creates a deployment package, and saves it in the `.aws-sam/build` folder.

The first command will build the source of your application. The second command will package and deploy your application to AWS, with a series of prompts:

* **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching your project name.
* **AWS Region**: The AWS region you want to deploy your app to.
* **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
* **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this example, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modifies IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
* **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to your application.

## Use the SAM CLI to build locally

Build the Lambda functions in your application with the `sam build --use-container` command.

```bash
VBliss_Blog$ sam build --use-container
```

The SAM CLI installs dependencies defined in `functions/*/requirements.txt`, creates a deployment package, and saves it in the `.aws-sam/build` folder.

## Add a resource to your application
The application template uses AWS Serverless Application Model (AWS SAM) to define application resources. AWS SAM is an extension of AWS CloudFormation with a simpler syntax for configuring common serverless application resources such as functions, triggers, and APIs. For resources not included in [the SAM specification](https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md), you can use standard [AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html) resource types.

## Fetch, tail, and filter Lambda function logs

To simplify troubleshooting, SAM CLI has a command called `sam logs`. `sam logs` lets you fetch logs generated by your deployed Lambda function from the command line. In addition to printing the logs on the terminal, this command has several nifty features to help you quickly find the bug.

`NOTE`: This command works for all AWS Lambda functions; not just the ones you deploy using SAM.

```bash
VBliss_Blog$ sam logs -n StockCheckerFunction --stack-name "vbliss_blog" --tail
```

You can find more information and examples about filtering Lambda function logs in the [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

## 7. Update the Code

### Add resources to your application

The application template uses AWS Serverless Application Model (AWS SAM) to define application resources. AWS SAM is an extension of AWS CloudFormation with a simpler syntax for configuring common serverless application resources such as functions, triggers, and APIs. For resources not included in [the SAM specification](https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md), you can use standard [AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html) resource types.

### Build your Docker image

```bash
sam build --use-container
```

### Deploy your SAM Application

```bash
sam deploy
```

## Resources

See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) for an introduction to SAM specification, the SAM CLI, and serverless application concepts.

Next, you can use AWS Serverless Application Repository to deploy ready to use Apps that go beyond hello world samples and learn how authors developed their applications: [AWS Serverless Application Repository main page](https://aws.amazon.com/serverless/serverlessrepo/)
