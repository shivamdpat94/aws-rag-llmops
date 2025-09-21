# Allow S3 bucket to invoke the Lambda
resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.app.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.docs.arn
}

# Ensure S3 wires the trigger only after permission exists
resource "aws_s3_bucket_notification" "docs_events" {
  bucket = aws_s3_bucket.docs.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.app.arn
    events              = ["s3:ObjectCreated:*"]
    # Optional filters:
    # filter_suffix = ".txt"
    # filter_prefix = "incoming/"
  }

  depends_on = [aws_lambda_permission.allow_s3_invoke]
}
