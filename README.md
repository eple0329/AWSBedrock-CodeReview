Here's the English translation of the content, with some minor adaptations:

# Bedrock CodeReview Bot

Translation
🇰🇷[한국어](https://github.com/eple0329/AWSBedrock-CodeReview/blob/main/README-KO.md) | [ENGLISH](https://github.com/eple0329/AWSBedrock-CodeReview/blob/main/README.md)

## Overview

This is a Bot that performs CodeReview for Github PRs using Bedrock, one of the AWS services.

## How To Use?

```yml
name: PR Review Bot

on:
  pull_request:
    types: [ opened, synchronize ]

permissions:
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: AWS Bedrock Code Review Action
        uses: eple0329/AWSBedrock-CodeReview@latest
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}
          github-token: ${{ secrets.GITHUB_TOKEN }} # Variable provided by default in Github
          # Optional
          model: 'amazon.titan-text-premier-v1:0' # Default: Anthropic Haiku
          max-tokens: 1000 # Default: 1000
          language: 'Korean' # Default: English
          prompt: "your Custom Prompt"
```

### Permission

```yml
permissions:
  pull-requests: write
```

- **Write permission** for pull-requests is mandatory.
- Without this permission, you may encounter errors such as:
    - `"Resource not accessible by integration"`
    - `"HttpError: 403 Forbidden"`

### Environments

- aws-access-key-id, aws-secret-access-key
    - These are authentication credentials to access the AWS Bedrock service.
    - They are the access keys of a user created in AWS IAM (Identity and Access Management).
    - AWS_ACCESS_KEY_ID represents the ID of the access key, and AWS_SECRET_ACCESS_KEY represents the secret access key.
    - Minimum required permission for this account: `bedrock:InvokeModel`

  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "InvokeModelAccess",
        "Effect": "Allow",
        "Action": "bedrock:InvokeModel",
        "Resource": "*"
      }
    ]
  }
  ```

- aws-region
    - Specifies the region where AWS services will be used.
    - 'us-east-1', 'ap-northeast-3' etc...
    - Please use a region that supports the Bedrock service. ([Reference](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-regions.html))

- github-token
    - This is an authentication token for using the GitHub API.
    - It uses the token automatically provided by GitHub Actions. **(You don't need to add it to secrets.)**
    - It's used for commenting on pull requests or updating statuses.

#### [Optional]

- model
    - Specifies the AWS Bedrock model to use.
    - The default is Anthropic's Haiku model.
    - **Currently available models are AWS Titan Text / Anthropic types.**
        - Other models might be usable, but we can't guarantee as they haven't been tested.
- language
    - Specifies the language of the code review response.
    - The default is English.

- prompt
    - This is a custom prompt to be passed to the model.
    - You can specify the style, focus, and details of the code review.
    - For example, you can set it as "You are a senior backend engineer. Please review the following code changes and
      provide a detailed review in terms of security, performance, and readability."

## Contributing

Do you have any suggestions for this project? We welcome proposals in all areas, including feature suggestions, bug
reports, and documentation modifications!

## Credit

This project was inspired by [ChatGPT-CodeReview](https://github.com/anc95/ChatGPT-CodeReview).