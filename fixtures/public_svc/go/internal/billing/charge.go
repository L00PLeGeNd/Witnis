package billing

type ChargeRequest struct {
	AmountCents int
	Token       string
}

func Authorize(req ChargeRequest) bool {
	return req.AmountCents > 0 && req.Token != ""
}
