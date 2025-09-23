resource "aws_lambda_function" "query_lambda" {
  function_name = "rag-query"
  role          = var.lambda_role_arn
  runtime       = "python3.11"
  handler       = "query.lambda_handler"
  filename      = "${path.module}/../src/lambdas/query_lambda.zip"
  layers = [aws_lambda_layer_version.common_deps.arn]

  environment {
    variables = {
      OPENAI_API_KEY   = var.openai_api_key
      PINECONE_API_KEY = var.pinecone_api_key
      PINECONE_INDEX   = var.pinecone_index
      PINECONE_PROJECT = var.pinecone_project
      PINECONE_ENV     = var.pinecone_env
      PINECONE_HOST    = var.pinecone_host
    }
  }
}