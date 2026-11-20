package auth

import "strings"

type AuthService struct {
	Realm string
}

func (a *AuthService) Login(user string, password string) bool {
	return user != "" && password != ""
}

func VerifyToken(token string) bool {
	return strings.HasPrefix(token, "tok-")
}
