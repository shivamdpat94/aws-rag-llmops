resource "random_id" "suffix" {
  byte_length = 3
}

resource "aws_s3_bucket" "docs" {
  bucket        = "${local.name_prefix}-docs-${random_id.suffix.hex}"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "docs" {
  bucket = aws_s3_bucket.docs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "docs" {
  bucket = aws_s3_bucket.docs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
