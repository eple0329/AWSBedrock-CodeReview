import botocore.session, botocore.exceptions
import urllib.request, urllib.error
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
anthropic_model = os.environ['INPUT_ANTHROPIC_MODEL']
max_tokens = os.environ['INPUT_MAX_TOKENS']


def get_pr_diff():
    api_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"

    # GitHub API 요청 헤더
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.diff"
    }

    # API 요청 생성
    req = urllib.request.Request(api_url, headers=headers)

    try:
        # API 요청 실행
        with urllib.request.urlopen(req) as response:
            # 응답 읽기
            response_data = response.read()

            # 응답 디코딩 (UTF-8 사용)
            response_text = response_data.decode('utf-8')

            # 상태 코드 확인
            status_code = response.getcode()

            print(f"Status Code: {status_code}")
            print(f"Response: {response_text[:100]}...")  # 처음 100자만 출력

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(f"Reason: {e.reason}")
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")


def analyze_with_bedrock(diff):
    formatted_prompt = f"Human: You're a senior backend engineer. Below there is a code diff please help me do a code review.\n\nFormat:\n- Numbering issues, specify file. Use markdown, headers, code blocks.\n- Suggest improvements/examples.\n- Be constructive.\n\nPR diff:\n\n{diff}\n\nProvide detailed review. Please answer to korean Assistant:"

    # botocore 세션 생성
    session = botocore.session.get_session()

    session.set_credentials(
        access_key=access_key,
        secret_key=secret_key
    )

    # Bedrock 런타임 클라이언트 생성
    client = session.create_client('bedrock-runtime', region_name=aws_region)

    # 요청 본문 생성
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

    try:
        # Bedrock 모델 호출
        response = client.invoke_model(
            modelId=anthropic_model,
            contentType='application/json',
            accept='application/json',
            body=request_body
        )

        for event in response['body']:
            # 바이트 문자열을 일반 문자열로 디코딩
            response_str = event.decode('utf-8')

            # JSON 파싱
            response_json = json.loads(response_str)

            # content의 text 추출
            content_text = response_json['content'][0]['text']

            return content_text

    except botocore.exceptions.ClientError as error:
        print("An error occurred:", error)

    except (KeyError, IndexError) as e:
        print("An error occurred:", e)


def post_review(comment):
    # GitHub API 엔드포인트
    api_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    # GitHub API 요청 헤더
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github-commitcomment.raw+json",
        "Content-Type": "application/json"
    }

    data = {
        "body": "# [REVIEW_BOT]\n" + comment
    }

    # JSON 데이터를 인코딩
    data = json.dumps(data).encode('utf-8')

    # 요청 객체 생성
    req = urllib.request.Request(api_url, data=data, headers=headers, method='POST')

    try:
        # API 요청 보내기
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 201:
                print("Comment posted successfully!")
            else:
                print(f"Failed to post comment: {response.getcode()}")
                print(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(e.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")


if __name__ == "__main__":
    diff = get_pr_diff()
    review_comments = analyze_with_bedrock(diff)
    post_review(review_comments)
