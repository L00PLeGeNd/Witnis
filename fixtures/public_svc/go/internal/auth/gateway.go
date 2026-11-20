package auth

import "strings"

type Gateway struct {
	Realm string
}

func (g *Gateway) Issue(user string) string {
	return "tok-" + user
}

func (g *Gateway) Verify(token string) bool {
	return strings.HasPrefix(token, "tok-")
}
