# Deploy notes (do not deploy without credentials / Bedrock unlock)

## Local image build

```bash
docker build -t sentinel:local .
docker run --rm -p 8000:8000 \
  -e DATABASE_URL \
  -e EMBEDDINGS_BACKEND=fake \
  -e LLM_BACKEND=fake \
  -e REMEDIATE_MODE=local \
  sentinel:local
```

Open http://localhost:8000 — product UI at `/`, API under `/api/*`, health at `/health`.

## App Runner / Fargate (when ready)

1. Push image to ECR in `us-east-1` (Bedrock region).
2. Create App Runner service (or ECS Fargate + ALB) with env:
   - `DATABASE_URL` from Secrets Manager / SSM (not plaintext in task def if possible)
   - `EMBEDDINGS_BACKEND` / `LLM_BACKEND` (`fake` until Bedrock quotas unlock)
   - `REMEDIATE_MODE=local` until executor Lambda is deployed
   - optional `S3_BUCKET`
3. Health check path: `/health`
4. Public demo URL is the App Runner default domain (or custom domain).

## Not done here

- Actual ECR push / App Runner create (needs AWS console + credentials)
- Bedrock Claude / Titan unlock (see `aws_setup.md`)
- Lambda Function URL for ingest (handler exists under `lambdas/ingest`)
