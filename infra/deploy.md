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

## ECS Express Mode (when ready)

App Runner is sunset (April 30, 2026) — do not create new App Runner services; use ECS Express Mode in `us-east-1` (Bedrock region).

1. Build locally and push to ECR (`sentinel` repo); set `$IMAGE_URI` to the pushed image.
2. In `--primary-container`, split env:
   - `environment` (non-secrets): `EMBEDDINGS_BACKEND=fake`, `LLM_BACKEND=fake`, `REMEDIATE_MODE=local`, `AWS_REGION=us-east-1`, `S3_BUCKET=sentinel-artifacts-951532862171-us-east-1`
   - `secrets` (`valueFrom` Secrets Manager, never plaintext): `DATABASE_URL` — and `SENTINEL_READ_USER` / `SENTINEL_READ_PASSWORD` the same way if the read path needs them
3. Health check path `/health`, container port `8000`:

```bash
aws ecs create-express-gateway-service \
  --service-name sentinel \
  --execution-role-arn $EXECUTION_ROLE_ARN \
  --infrastructure-role-arn $INFRA_ROLE_ARN \
  --primary-container '{"image":"$IMAGE_URI","containerPort":8000,"environment":[{"name":"EMBEDDINGS_BACKEND","value":"fake"},{"name":"LLM_BACKEND","value":"fake"},{"name":"REMEDIATE_MODE","value":"local"},{"name":"AWS_REGION","value":"us-east-1"},{"name":"S3_BUCKET","value":"sentinel-artifacts-951532862171-us-east-1"}],"secrets":[{"name":"DATABASE_URL","valueFrom":"$DATABASE_URL_SECRET_ARN"}]}'
```

## Not done here

- Actual ECR push / Express Mode service create (needs credentials + roles)
- Bedrock Claude / Titan unlock (see `aws_setup.md`)
- Lambda Function URL for ingest (handler exists under `lambdas/ingest`)
