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
max_tokens = os.environ['INPUT_MAX_TOKENS']

input_prompt = os.environ['INPUT_PROMPT']
language = os.environ['INPUT_LANGUAGE']


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
        print(f"Response: {response.text[:100]}...")  # 처음 100자만 출력

        return response.text

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def analyze_with_bedrock(diff):
    # botocore 세션 생성
    session = botocore.session.get_session()

    session.set_credentials(
        access_key=access_key,
        secret_key=secret_key
    )

    # Bedrock 런타임 클라이언트 생성
    client = session.create_client('bedrock-runtime', region_name=aws_region)

    prompt = input_prompt + f" Please answer to {language}."
    prompt = prompt + f" PR diff:\n\n{diff}"

    print(prompt)

    provider = model.split('.')[0]
    request_body = ""

    if provider == 'anthropic':
        formatted_prompt = "Human: " + prompt + " Assistant:"

        request_body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": int(max_tokens),
            "messages": [
                {
                    "role": "user",
                    "content": formatted_prompt
                }
            ]
        })

    if provider == 'amazon':
        formatted_prompt = "User: " + prompt + " \n Bot:"

        request_body = json.dumps({
            "inputText": formatted_prompt,
            "textGenerationConfig": {
                "temperature": 0.7,
                "topP": 0.9,
                "maxTokenCount": int(max_tokens)
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

        if provider == 'anthropic':
            response_body = b''
            for event in response['body']:
                response_body += event
            # 바이트 문자열을 일반 문자열로 디코딩
            response_str = response_body.decode('utf-8', errors='ignore')
            print(response_str)

            # JSON 파싱
            response_json = json.loads(response_str)

            # content의 text 추출
            content_text = response_json['content'][0]['text']

            return content_text

        if provider == 'amazon':
            response_body = json.loads(response.get("body").read())
            finish_reason = response_body.get("error")  # AWS 에러

            if finish_reason is not None:
                raise f"Text generation error. Error is {finish_reason}"

            print(f"Input token count: {response_body['inputTextTokenCount']}")
            for result in response_body['results']:
                print(f"Token count: {result['tokenCount']}")
                #print(f"Output text: {result['outputText']}")
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
        "body": "# [REVIEW_BOT]\n" + comment
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
