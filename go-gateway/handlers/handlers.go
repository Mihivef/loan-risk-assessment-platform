package handlers

import (
	"fmt"

	"github.com/gin-gonic/gin"
	"loan-risk/middleware"
	"loan-risk/models"
	"loan-risk/service"
	"net/http"
	"strconv"
)

type Handler struct {
	Service service.LoanServicer
}

func New(s service.LoanServicer) *Handler {
	return &Handler{Service: s}
}

func (h *Handler) SubmitApplication(c *gin.Context) {
	var req models.SubmitApplicationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "validation failed",
			"details": err.Error(),
		})
		return
	}

	user, _ := c.Get("user")
	u := user.(middleware.UserInfo)

	app, summary, err := h.Service.SubmitApplication(req, u.Username)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "failed to process application",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message":     "application processed",
		"application": app,
		"pipeline":    summary,
	})

}
func (h *Handler) ListApplications(c *gin.Context) {
	app := h.Service.ListApplications(c.Query("status"))

	c.JSON(http.StatusOK, gin.H{
		"total":        len(app),
		"applications": app,
	})
}
func (h *Handler) GetApplication(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))

	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "id must be a number",
		})
		return
	}

	app, ok := h.Service.GetApplication(id)

	if !ok {
		c.JSON(http.StatusNotFound, gin.H{
			"error": fmt.Sprintf("application %d not found", id),
		})
		return
	}

	c.JSON(http.StatusOK, app)
}

func (h *Handler) UpdateStatus(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))

	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "id must be a number",
		})
		return
	}

	var req models.UpdateStatusRequest

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "validation failed",
			"details": err.Error(),
		})
		return
	}

	app, ok := h.Service.UpdateStatus(id, req.Status, req.Notes)

	if !ok {
		c.JSON(http.StatusNotFound, gin.H{
			"error": fmt.Sprintf("application %d not found", id),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":     "status updated",
		"application": app,
	})
}
func (h *Handler) GetDashboardStats(c *gin.Context) {
	c.JSON(http.StatusOK, h.Service.Stats())
}
func (h *Handler) CalculateEMI(c *gin.Context) {
	principal, _ := strconv.ParseFloat(c.Query("principal"), 64)
	rate, _ := strconv.ParseFloat(c.Query("rate"), 64)
	tenure, _ := strconv.Atoi(c.Query("tenure_months"))

	if principal <= 0 || rate <= 0 || tenure <= 0 {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "provide principal, rate, and tenure_months",
		})
		return
	}

	result, err := h.Service.CalculateEMI(principal, rate, tenure)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "failed to calculate EMI",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, result)
}
func HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "ok",
		"service": "go-gateway",
		"port":    8080,
	})
}
