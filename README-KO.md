# Bedrock CodeReview Bot

Translation
🇰🇷[한국어](https://github.com/eple0329/AWSBedrock-CodeReview/blob/main/README-KO.md) | [ENGLISH](https://github.com/eple0329/AWSBedrock-CodeReview/blob/main/README.md)

## Overview

AWS 서비스 중 하나인 Bedrock을 사용하여 Github PR의 CodeReview를 해주는 Bot입니다.

## How To Use?

``` yml
name: PR Review Bot

on:
  pull_request:
    types: [opened, synchronize]
    
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
          github-token: ${{ secrets.GITHUB_TOKEN }} # Github에서 기본적으로 제공하는 변수
          # Optional
          model: 'amazon.titan-text-premier-v1:0' # Default: Anthropic Haiku
          max-tokens: 1000 # Default: 1000
          language: 'Korean' # Default: English
          prompt: "your Custom Prompt"



```

### Permission

``` yml
permissions:
  pull-requests: write
```

- pull-requests에 대한 **Write 권한**이 반드시 있어야 합니다.
- 해당 권한이 없다면 다음과 같은 에러가 발생할 수 있습니다.
    - `"Resource not accessible by integration"`
    - `"HttpError: 403 Forbidden"`

### Environments

- aws-access-key-id, aws-secret-access-key

    - AWS Bedrock 서비스에 접근하기 위한 인증 정보입니다.
    - AWS IAM(Identity and Access Management)에서 생성한 사용자의 액세스 키입니다.
    - AWS_ACCESS_KEY_ID는 액세스 키의 ID를, AWS_SECRET_ACCESS_KEY는 비밀 액세스 키를 나타냅니다.
    - 해당 계정에 필요한 최소 권한: `bedrock:InvokeModel`

  ``` json
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
    - AWS 서비스를 사용할 리전을 지정합니다.
    - 'us-east-1', 'ap-northeast-3' etc...
    - Bedrock 서비스를 지원하는 리전을 사용해주세요. ([참고](https://docs.aws.amazon.com/ko_kr/bedrock/latest/userguide/bedrock-regions.html))

- github-token
    - GitHub API를 사용하기 위한 인증 토큰입니다.
    - GitHub Actions에서 자동으로 제공하는 토큰을 사용합니다. **(secrets에 추가하지 않아도 됩니다.)**
    - 풀 리퀘스트에 코멘트를 달거나 상태를 업데이트하는 데 사용됩니다.

#### [Optional]

- model
    - 사용할 AWS Bedrock 모델을 지정합니다.
    - 기본값은 Anthropic의 Haiku 모델입니다.
    - **현재 사용 가능한 모델은 AWS Titan Text / Anthropic 종류의 모델입니다.**
        - 다른 모델도 사용이 가능할 수도 있지만, 테스트해보지 않아 보장할 수 없습니다.
- language
    - 코드 리뷰 응답의 언어를 지정합니다.
    - 기본값은 영어(English)입니다.

- prompt
    - 모델에 전달할 사용자 정의 프롬프트입니다.
    - 코드 리뷰의 스타일, 포커스, 세부 사항 등을 지정할 수 있습니다.
    - 예를 들어, "당신은 시니어 백엔드 엔지니어입니다. 아래의 코드 변경사항을 검토하고 보안, 성능, 가독성 측면에서 상세한 리뷰를 제공해주세요." 와 같이 설정할 수 있습니다.

## Contributing

본 프로젝트에 제안하고 싶은 점이 있나요? 기능 제안, 버그 제보, 문서 수정 등 모든 부분에서의 제안을 환영합니다!

## Credit

이 프로젝트는 [ChatGPT-CodeReview](https://github.com/anc95/ChatGPT-CodeReview)에서 영감을 받아 개발되었습니다.