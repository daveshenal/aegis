variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "aegis"
}

variable "ecr_repo_name" {
  type    = string
  default = "aegis"
}

variable "s3_bucket_name" {
  type    = string
  default = "aegis-docs-410376035918"
}