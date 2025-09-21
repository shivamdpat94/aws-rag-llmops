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
