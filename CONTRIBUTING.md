# Contributing Guidelines

Thank you for your interest in contributing to our project. Whether it's a bug report, new feature, correction, or additional
documentation, we greatly value feedback and contributions from our community.

Please read through this document before submitting any issues or pull requests to ensure we have all the necessary
information to effectively respond to your bug report or contribution.

## Table of Contents
1. [Reporting Bugs/Feature Requests](#Reporting)
2. [Contributing via Pull Requests](#Pulls)
4. [Linking External Example](#Extern)
5. [Style and Formatting](#Style)
6. [Finding Contributions to Work On](#Finding)
9. [Security Issue Notifications](#Security)

## Reporting Bugs/Feature Requests <a name="Reporting"></a>

We welcome you to use the GitHub issue tracker to report bugs or suggest features.

When filing an issue, please check [existing open](https://github.com/amaynez/Make.com-to-AWS/issues), or [recently closed](https://github.com/amaynez/Make.com-to-AWS/issues?utf8=%E2%9C%93&q=is%3Aissue%20is%3Aclosed%20), issues to make sure somebody else hasn't already reported the issue. Please try to include as much information as you can. Details like these are incredibly useful:

* A reproducible test case or series of steps
* The version of our code being used
* Any modifications you've made relevant to the bug
* Anything unusual about your environment or deployment

## Contributing via Pull Requests <a name="Pulls"></a>
Contributions via pull requests are much appreciated. Before sending us a pull request, please ensure that:

1. You are working against the latest source on the *master* branch.
2. You check existing open, and recently merged, pull requests to make sure someone else hasn't addressed the problem already.

To send us a pull request, please:

1. Fork the repository.
2. Modify the source; please focus on the specific change you are contributing. If you also reformat all the code, it will be hard for us to focus on your change.
3. Ensure local tests pass tests 
4. Commit to your fork using clear commit messages.
5. Send us a pull request, answering any default questions in the pull request interface.
6. Pay attention to any automated CI failures reported in the pull request, and stay involved in the conversation.

GitHub provides additional document on [forking a repository](https://help.github.com/articles/fork-a-repo/) and
[creating a pull request](https://help.github.com/articles/creating-a-pull-request/).

### Added Value
As an official learning resource, it is important that any new examples add value to our learning resources. This means that it should not duplicate an existing example, and cover one of the following topics:

* Document a common infrastructure pattern - _(static website, cron triggered lambda, etc.)_
* Outline usage of an L2 construct
* Cover a less-obvious implementation of one or more constructs - _(cross-stack resource sharing, escape hatches, using SSM values during synthesis, etc.)_

When we are considering merging a new contribution we will review the above criteria as well as evaluating quality based on the criteria in the following sections.

### Components

When adding a new example, there are several required components. The majority of these will be added when running `sam build --use-container`.

1. General Structure

The best way to create the structure for the new example to be added is to run `sam init` on an empty directory with the example name. This will generate all language-specific components needed for your new example. Please keep the suggested structure for the application (eg. typescript apps start in `./bin/example-name.ts`, and store the stack/s in `./lib/example-name-stack.ts`).

When submitting the PR, please ensure that the directory includes all relevant package manager and configuration files so that someone else viewing it only needs to run the build commands and `sam deploy` to get the example running.

2. `README.md`

Every example needs a comprehensive README at the root of its directory. This README can vary depending on the example, but has several required components:
  - Stability Banner: You can use the banner code below to indicate whether an example consists of modules that are "Stable", "Dev-Preview", or "Cfn-Only" (for more information on state, see the [Module Lifecycle guide](https://github.com/aws/aws-cdk-rfcs/blob/master/text/0107-construct-library-module-lifecycle.md). Please reference the lowest common denominator (if all modules are stable except for one that is dev-preview, you must mark the example as dev-preview)

    - __Stable__
```md
<!--BEGIN STABILITY BANNER-->
---

![Stability: Stable](https://img.shields.io/badge/stability-Stable-success.svg?style=for-the-badge)

> **This is a stable example. It should successfully build out of the box**
>
> This example is built on Construct Libraries marked "Stable" and does not have any infrastructure prerequisites to build.
---
<!--END STABILITY BANNER-->
```

- __Dev Preview__
```md
<!--BEGIN STABILITY BANNER-->
---

![Stability: Developer Preview](https://img.shields.io/badge/stability-Developer--Preview-important.svg?style=for-the-badge)

> **This is an experimental example. It may not build out of the box**
>
> This example is built on Construct Libraries marked "Developer Preview" and may not be updated for latest breaking changes.
>
> It may additionally requires infrastructure prerequisites that must be created before successful build.
>
> If build is unsuccessful, please create an [issue](https://github.com/aws-samples/aws-cdk-examples/issues/new) so that we may debug the problem 
---
<!--END STABILITY BANNER-->
```

  - Overview: This should be a description of the example including, but not limited to, an overview of resources being created in the example, a description of any standard/common patterns being used, as well as the overall function of the example.
  - Structure: If the example is more complex than a single stack, or the stack contains more than a couple resources, please describe the structure of application being deployed. This can be as simple as a bulleted list of resources, or as intricate as a complete infrastructure diagram.
  - Build/Deploy: Finally, the README must include the basic build/deploy instructions required for that example in said language.

### Linking External Examples <a name="Extern"></a>

If you have an example project that is out of scope or too large for this repo based on the criteria listed above, but you still think it would be a good learning resource for CDK users, you may contribute it to this repo as an external link.

Simply create a Pull Request to the README of this repo, adding the link to your repo. The pull request can be used to discuss the function and content of the linked repo with the SAM team and other contributors.

## Style and Formatting <a name="Style"></a>

We strive to keep examples consistent in style and formatting. This hopefully makes navigating examples easier for users. Since the examples span different languages, we try to keep example code as idiomatic as possible.

New guidelines for various languages will be added as we define them.

## Finding Contributions to Work On <a name="Finding"></a>
Looking at the existing issues is a great way to find something to contribute on. As our projects, by default, use the default GitHub issue labels (enhancement/bug/duplicate/help wanted/invalid/question/wontfix), looking at any ['help wanted'](https://github.com/amaynez/Make.com-to-AWS/labels/help%20wanted) issues is a great place to start.

## Security Issue Notifications <a name="Security"></a>
If you discover a potential security issue in this project we ask that you please create a public github issue.
