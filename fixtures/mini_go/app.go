package main

import (
	"fmt"

	"example.com/mini_go/auth"
)

func main() {
	svc := auth.AuthService{Realm: "demo"}
	ok := svc.Login("alice", "secret")
	fmt.Println(ok, auth.VerifyToken("tok-1"))
}
