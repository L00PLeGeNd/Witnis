package main

import (
	"fmt"

	"example.com/public_svc/internal/auth"
)

func main() {
	g := &auth.Gateway{Realm: "public"}
	fmt.Println(g.Issue("alice"))
}
