// Cryptanalysis is a double-click app. It serves the dashboard and opens it
// in the default browser.
package main

import (
	_ "embed"
	"net"
	"net/http"
	"os/exec"
	"runtime"
)

//go:embed Cryptanalysis.html
var page []byte

func main() {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return
	}

	server := http.NewServeMux()
	server.HandleFunc("/", func(response http.ResponseWriter, _ *http.Request) {
		response.Header().Set("Content-Type", "text/html; charset=utf-8")
		response.Write(page)
	})
	go http.Serve(listener, server)

	openBrowser("http://" + listener.Addr().String() + "/")
	select {}
}

func openBrowser(address string) {
	switch runtime.GOOS {
	case "windows":
		exec.Command("rundll32", "url.dll,FileProtocolHandler", address).Start()
	case "darwin":
		exec.Command("open", address).Start()
	default:
		exec.Command("xdg-open", address).Start()
	}
}
