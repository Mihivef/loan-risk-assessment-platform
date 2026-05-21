FROM golang:1.23 AS builder

WORKDIR /app

COPY go.mod ./

RUN go get github.com/gin-gonic/gin@v1.9.1

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -o gateway .

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /app/gateway .
EXPOSE 8080
CMD ["./gateway"]
