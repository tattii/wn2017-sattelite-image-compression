package main

import (
	"fmt"
	"os"
	"encoding/binary"
)

func main(){
	flag := os.Args[1]
	input := os.Args[2]
	output := os.Args[3]

	if flag == "encode" {
		encode_file(input, output)
	}

}

func encode_file(input, output string){
	size, array := readBinary(input)

	out, _ := os.Create(output)
	defer out.Close()
	binary.Write(out, binary.LittleEndian, size)

	fmt.Println(size, array[:20])
}


func readBinary(filename string) (size int64, array []int16){
	fileinfo, _ := os.Stat(filename)
	size = fileinfo.Size()

	file, _ := os.Open(filename)
	defer file.Close()
	array = make([]int16, size / 2)
	binary.Read(file, binary.LittleEndian, &array)
	return
}

