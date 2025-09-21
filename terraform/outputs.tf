output "docs_bucket_name" {
  value = aws_s3_bucket.docs.bucket
}

output "lambda" {
  value = aws_lambda_function.app.function_name
}

# terraform/outputs.tf
output "app_lambda_name" {
  value = aws_lambda_function.app.function_name
}
