import re

import botocore.session, botocore.exceptions
import requests
import json
import os

# Github 환경 변수
github_token = os.environ['INPUT_GITHUB_TOKEN']
repo = os.environ['INPUT_GITHUB_REPOSITORY']
pr_number = os.environ['INPUT_PR_NUMBER']

# AWS 환경 변수
access_key = os.environ['INPUT_AWS_ACCESS_KEY_ID']
secret_key = os.environ['INPUT_AWS_SECRET_ACCESS_KEY']
aws_region = os.environ['INPUT_AWS_REGION']

# Bedrock 환경 변수
model = os.environ['INPUT_MODEL']
max_tokens = int(os.environ['INPUT_MAX_TOKENS'])

# 추가 환경 변수
input_prompt = os.environ['INPUT_PROMPT']
language = os.environ['INPUT_LANGUAGE']
title = os.environ['INPUT_TITLE']
temperature = float(os.environ['INPUT_TEMPERATURE'])
top_p = float(os.environ['INPUT_TOP_P'])
home_dir = os.environ['INPUT_HOME_DIRECTORY']


def get_pr_diff():
    api_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.diff"
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        print(f"Status Code: {response.status_code}")

        return filtering_diff(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def filtering_diff(diff):
    changed_files = set(re.findall(r'diff --git a/(.*?) b/', diff))
    print("changed_files:")
    for file in changed_files:
        print(f"- {file}")

    # 홈 디렉토리 내의 파일만 필터링하고 제외 파일 리스트에 없는 파일만 선택
    filtered_files = [
        file for file in changed_files if file.startswith(home_dir)
    ]

    print("Filtered changed files:")
    for file in filtered_files:
        print(f"- {file}")

    # 필터링된 파일만 포함하는 새로운 diff 생성
    filtered_diff = []
    current_file = None
    for line in diff.splitlines():
        if line.startswith('diff --git'):
            file_match = re.search(r'diff --git a/(.*?) b/', line)
            if file_match:
                current_file = file_match.group(1)

        if current_file in filtered_files:
            filtered_diff.append(line)
    return '\n'.join(filtered_diff)


def analyze_with_bedrock(diff):
    # botocore 세션 생성
    session = botocore.session.get_session()

    session.set_credentials(
        access_key=access_key,
        secret_key=secret_key
    )

    # Bedrock 런타임 클라이언트 생성
    client = session.create_client('bedrock-runtime', region_name=aws_region)

    system_prompt = input_prompt + f" Please answer to {language}. "

    provider = model.split('.')[0]
    request_body = ""

    if provider == 'anthropic':
        request_body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": diff
                }
            ]
        })

    if provider == 'amazon':
        request_body = json.dumps({
            "inputText": system_prompt + diff,
            "textGenerationConfig": {
                "temperature": temperature,
                "topP": top_p,
                "maxTokenCount": max_tokens
            }
        })

    try:
        # Bedrock 모델 호출
        response = client.invoke_model(
            modelId=model,
            contentType='application/json',
            accept='application/json',
            body=request_body
        )

        response_body = b''
        for event in response['body']:
            response_body += event

        # 바이트 문자열을 일반 문자열로 디코딩
        response_str = response_body.decode('utf-8', errors='ignore')
        response_json = json.loads(response_str)

        if provider == 'anthropic':
            # content의 text 추출
            content_text = response_json['content'][0]['text']

            return content_text

        if provider == 'amazon':
            finish_reason = response_json.get("error")  # AWS 에러
            if finish_reason is not None:
                raise f"Text generation error. Error is {finish_reason}"

            print(f"Input token count: {response_json['inputTextTokenCount']}")
            for result in response_json['results']:
                print(f"Token count: {result['tokenCount']}")
                return result['outputText']

    except botocore.exceptions.ClientError as error:
        print("An error occurred:", error)

    except (KeyError, IndexError) as e:
        print("An error occurred:", e)


def post_review(comment):
    api_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github-commitcomment.raw+json",
        "Content-Type": "application/json"
    }

    data = {
        "body": f"# {title}\n" + str(comment)
    }

    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()

        if response.status_code == 201:
            print("Comment posted successfully!")
        else:
            print(f"Failed to post comment: {response.status_code}")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    diff = get_pr_diff()
    review_comments = analyze_with_bedrock(diff)
    post_review(review_comments)
