variable "repo_name" {
  type = string
}

output "repository_url" {
  value = aws_ecr_repository.this.repository_url
}