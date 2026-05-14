package middleware

import (
	"github.com/gin-gonic/gin"
	"net/http"
)

type UserInfo struct {
	Username string
	Role     string
}

var validTokens = map[string]UserInfo{
	"token-customer":     {Username: "customer_1", Role: "customer"},
	"token-loan-officer": {Username: "officer_priya", Role: "loan_officer"},
	"token-admin":        {Username: "admin_arjun", Role: "admin"},
}

func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		token := c.GetHeader("Authorization")
		if token == "" {
			c.JSON(http.StatusUnauthorized, gin.H{
				"error": "Authorization header required",
				"hint":  "tokens: token-customer | token-loan-officer | token-admin",
			})
			c.Abort()
			return
		}
		user, ok := validTokens[token]
		if !ok {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
			c.Abort()
			return
		}
		c.Set("user", user)
		c.Next()
	}
}

func RequireRole(roles ...string) gin.HandlerFunc {
	allowed := make(map[string]bool)
	for _, r := range roles {
		allowed[r] = true
	}
	return func(c *gin.Context) {
		user, _ := c.Get("user")
		u := user.(UserInfo)
		if !allowed[u.Role] {
			c.JSON(http.StatusForbidden, gin.H{
				"error":     "insufficient permissions",
				"your_role": u.Role,
				"required":  roles,
			})
			c.Abort()
			return
		}
		c.Next()
	}
}
