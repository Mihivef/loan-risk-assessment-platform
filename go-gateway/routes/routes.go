package routes

import (
	"loan-risk/handlers"
	"loan-risk/middleware"
	"loan-risk/service"
	"loan-risk/store"

	"github.com/gin-gonic/gin"
)

func Setup(r *gin.Engine) {
	s := store.New()
	svc := service.New(s)
	h := handlers.New(svc)

	r.GET("/health", handlers.HealthCheck)

	r.GET("/api/emi", middleware.AuthMiddleware(), h.CalculateEMI)

	api := r.Group("/api")
	api.Use(middleware.AuthMiddleware())
	{
		api.POST("/applications", middleware.RequireRole("customer"), h.SubmitApplication)
		api.GET("/applications/:id",
			middleware.RequireRole("customer", "loan_officer", "admin"),
			h.GetApplication,
		)

		api.GET("/applications",
			middleware.RequireRole("loan_officer", "admin"),
			h.ListApplications,
		)
		api.PUT("/applications/:id/status",
			middleware.RequireRole("loan_officer", "admin"),
			h.UpdateStatus,
		)

		api.GET("/dashboard/stats",
			middleware.RequireRole("admin"),
			h.GetDashboardStats,
		)
	}
}
