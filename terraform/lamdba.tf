# ========== PACKAGE FUNCTION CODE ==========
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${abspath(path.module)}/../src/lambdas/app.py"
  output_path = "${path.module}/build/lambda.zip"
}

# Ensure build dir exists before first apply (create once manually in PowerShell):
# New-Item -ItemType Directory -Force .\terraform\build | Out-Null

# ========== LAYER FROM src/lambdas/python ==========
resource "aws_lambda_layer_version" "common_deps" {
  layer_name          = "${local.name_prefix}-deps"
  filename            = "${path.module}/../src/lambdas/layer.zip" # zip must contain top-level "python/" dir
  compatible_runtimes = ["python3.11"]
  description         = "Shared deps from dependencies/requirements.txt"
}

# ========== FUNCTION ==========
resource "aws_lambda_function" "app" {
  function_name = "${local.name_prefix}-app"
  role          = aws_iam_role.app_role.arn
  runtime       = "python3.11"
  handler       = "app.lambda_handler"

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  layers = [aws_lambda_layer_version.common_deps.arn]

environment {
  variables = {
    DOCS_BUCKET      = aws_s3_bucket.docs.bucket
    OPENAI_API_KEY   = var.openai_api_key
    PINECONE_API_KEY = var.pinecone_api_key
    PINECONE_ENV     = var.pinecone_env
    PINECONE_INDEX   = "${local.name_prefix}-docs"

    # NEW — tame the embedding burst while testing
    EMB_MODEL        = "text-embedding-3-small"
    EMB_BATCH_SIZE   = "8"
    EMB_MAX_RETRIES  = "6"
  }
}


}