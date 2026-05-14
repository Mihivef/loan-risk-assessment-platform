package main

import (
	"fmt"

	"loan-risk/db"
	"loan-risk/models"
	"loan-risk/routes"

	"github.com/gin-gonic/gin"
)

func main() {

	db.Connect()
	db.DB.AutoMigrate(&models.LoanApplication{})
	r := gin.Default()
	routes.Setup(r)

	fmt.Println()
	fmt.Println("  ┌────────────────────────────────────────────────────────────┐")
	fmt.Println("  │       Loan Risk Assessment Platform — Go Gateway :8080    │")
	fmt.Println("  ├────────────────────────────────────────────────────────────┤")
	fmt.Println("  │  Orchestrates:                                            │")
	fmt.Println("  │    Python FastAPI   :8000  (ML credit scoring + fraud)    │")
	fmt.Println("  │    Java Spring Boot :8081  (policy engine + EMI)          │")
	fmt.Println("  ├────────────────────────────────────────────────────────────┤")
	fmt.Println("  │  GET    /health                         public            │")
	fmt.Println("  │  GET    /api/emi?principal=&rate=&tenure_months=  auth    │")
	fmt.Println("  │  POST   /api/applications               customer          │")
	fmt.Println("  │  GET    /api/applications               loan_officer      │")
	fmt.Println("  │  GET    /api/applications/:id           all roles         │")
	fmt.Println("  │  PUT    /api/applications/:id/status    loan_officer      │")
	fmt.Println("  │  GET    /api/dashboard/stats            admin             │")
	fmt.Println("  ├────────────────────────────────────────────────────────────┤")
	fmt.Println("  │  Tokens: token-customer | token-loan-officer | token-admin│")
	fmt.Println("  └────────────────────────────────────────────────────────────┘")
	fmt.Println()

	r.Run(":8080")
}
