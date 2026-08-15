# AWS setup (Sentinel)

Working region: **us-east-1**. Account: `951532862171`.

## Done

### S3 artifacts bucket

- Name: `sentinel-artifacts-951532862171-us-east-1`
- Region: `us-east-1`
- Private (all public access blocked), SSE-S3 (`AES256`)
- Tags: `project=sentinel`, `purpose=artifacts`

Set in `.env` (not a secret):

```env
S3_BUCKET=sentinel-artifacts-951532862171-us-east-1
AWS_REGION=us-east-1
```

Use for raw diagnostic dumps and postmortem markdown. Knowledge embeddings still live in CockroachDB.

### Local AWS auth

```bash
aws login          # browser SSO / identity center if configured
aws sts get-caller-identity
```

Prefer short-lived creds over long-lived access keys. Root is fine for hackathon smoke only.

## Blocked: Bedrock model access

As of 2026-07-23 on this account:

| Model | Availability API | Invoke |
| --- | --- | --- |
| `amazon.titan-embed-text-v2:0` | `authorizationStatus: NOT_AUTHORIZED` | `ValidationException: Operation not allowed` |
| Anthropic Claude (e.g. Haiku 4.5) | agreement `NOT_AVAILABLE`, `NOT_AUTHORIZED` | blocked until FTU form |

Root cause signal: Service Quotas show **0** on-demand RPM/TPM for Titan Text Embeddings V2 (and many other Bedrock models). That matches `Operation not allowed` even though models list as ACTIVE in the catalog.

CLI attempts:

- `put-use-case-for-model-access` → `ValidationException: Your account is not authorized to perform this action. Please create a support case...`
- `create-foundation-model-agreement` → `AccessDeniedException: You have not filled out the request form`

Until unlocked, keep:

```env
EMBEDDINGS_BACKEND=fake
LLM_BACKEND=fake
```

### Human steps to unlock

1. Open [AWS Support Center](https://console.aws.amazon.com/support/home) (Account and billing cases are free; the Support API needs a paid plan).
2. Create a case — prefer **Account and billing** if Service limit increase is unavailable on Free Plan.
3. Paste the request below (account `951532862171`, region `us-east-1`).
4. After Support clears the restriction, open **Amazon Bedrock → Model access / Model catalog** in `us-east-1`.
5. Submit the Anthropic first-time use (FTU) form in the console (or retry `put-use-case-for-model-access`).
6. Accept the Claude marketplace agreement if prompted.
7. Smoke test:

```bash
# Titan
printf '%s' '{"inputText":"hello","dimensions":1024}' > /tmp/titan-in.json
aws bedrock-runtime invoke-model \
  --region us-east-1 \
  --model-id amazon.titan-embed-text-v2:0 \
  --content-type application/json --accept application/json \
  --body fileb:///tmp/titan-in.json /tmp/titan-out.json

# Then flip backends in .env (do not commit .env)
EMBEDDINGS_BACKEND=bedrock
LLM_BACKEND=bedrock
```

Optional model override:

```env
BEDROCK_LLM_MODEL=anthropic.claude-haiku-4-5-20251001-v1:0
```

#### Paste into the Support case

**Subject:** Enable Amazon Bedrock model access (Titan Embeddings V2 + Anthropic Claude)

**Body:**

```
Account ID: 951532862171
Region: us-east-1
Use case: Hackathon project "Sentinel" (CockroachDB x AWS) — autonomous DB reliability agent.
Public repo: https://github.com/himxsh/Sentinel

What we need:
1. On-demand inference access for amazon.titan-embed-text-v2:0 (text embeddings, 1024 dims).
2. Ability to submit the Anthropic first-time use (FTU) form and then invoke Claude on Bedrock (e.g. anthropic.claude-haiku-4-5-20251001-v1:0 or Claude 3.5 Sonnet).

What fails today:
- bedrock-runtime InvokeModel for amazon.titan-embed-text-v2:0 returns ValidationException: Operation not allowed.
- get-foundation-model-availability shows authorizationStatus NOT_AUTHORIZED for Titan Embed Text v2 and Claude Haiku 4.5.
- Service Quotas for "On-demand model inference requests per minute for Amazon Titan Text Embeddings V2" is 0.0.
- put-use-case-for-model-access returns ValidationException: Your account is not authorized to perform this action. Please create a support case...
- create-foundation-model-agreement for Claude fails with AccessDeniedException: You have not filled out the request form.

Please enable Bedrock foundation-model access / raise the Titan Embeddings V2 on-demand quota above 0, and authorize PutUseCaseForModelAccess so we can complete Anthropic FTU.

Expected volume is hackathon-scale smoke tests only (low RPM). Billing contact and payment method are already on the account.
```

## IAM (minimal local / Lambda)

For a dedicated IAM user or role later (not required while using root login for smoke):

- `bedrock:InvokeModel` on the Titan + Claude model ARNs in `us-east-1`
- `s3:PutObject`, `s3:GetObject` on `arn:aws:s3:::sentinel-artifacts-951532862171-us-east-1/*`
- For third-party Bedrock marketplace subscribe (Claude): `aws-marketplace:Subscribe`, `ViewSubscriptions`, `Unsubscribe`

## Lambdas (code in repo, not deployed yet)

- `lambdas/ingest/handler.py` — normalize alert → `handle_alert` or `AGENT_URL`
- `lambdas/executor/handler.py` — allow-listed remediation

Deploy when you want a public ingest URL; local `REMEDIATE_MODE=local` is enough for demos.

## App Runner / public demo URL

No Dockerfile yet. Prefer App Runner when deploying the FastAPI app + fake or live Bedrock backends. Needs `DATABASE_URL` as a secret and `S3_BUCKET` / `AWS_REGION` as env.
