variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "aws-rag"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "openai_api_key" {
  type = string
}

variable "pinecone_api_key" {
  type = string
}

variable "pinecone_env" {
  type = string
}

variable "lambda_role_arn" {
  description = "IAM role ARN for Lambda execution"
  type        = string
}

variable "pinecone_index" {
  description = "Name of the Pinecone index"
  type        = string
}

variable "pinecone_project" {
  description = "Pinecone project ID"
  type        = string
}

variable "pinecone_host" {
  description = "Full Pinecone host URL (e.g. https://index1-xxxx.svc.us-east-1-aws.pinecone.io)"
  type        = string
}

