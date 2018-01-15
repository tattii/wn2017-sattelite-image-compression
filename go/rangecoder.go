package main

import (
	"fmt"
	"os"
	"encoding/binary"
)

const MAX_RANGE uint32 = 0xffffffff
const MIN_RANGE uint32 = MAX_RANGE / 256
const MASK      uint32 = 0xfffffff
const SHIFT uint = 24

func main(){
	flag := os.Args[1]
	input := os.Args[2]
	output := os.Args[3]

	if flag == "encode" {
		encode_file(input, output)
	}else if flag == "decode" {
		decode_file(input, output)
	}
}


//---------------------------------------------------------
// encode
//---------------------------------------------------------
func encode_file(input, output string){
	size, array := readBinary(input)

	// sub
	//array2 := make([]uint16, len(array))
	//array2[0] = array[0] + 1024
	//for i := 1; i < len(array); i++ {
	//	array2[i] = array[i] - array[i - 1] + 1024
	//}

	out, _ := os.Create(output)
	//defer out.Close()
	binary.Write(out, binary.LittleEndian, size / 2)

	fmt.Println(size)
	encode(array, out)
}

func encode(array []uint16, out *os.File){
	count := count_table(array)

	encoder := &Encoder{}
	encoder.init(out)
	encoder.init_count_table(count)
	encoder.write_count_table()

	for _, x := range array {
		encoder.encode(x)
	}
	encoder.finish()
}

func count_table(array []uint16) ([]uint32){
	count := make([]uint32, 256 * 256)
	for _, x := range array {
		count[x] += 1
	}
	return count
}


type Encoder struct {
	file *os.File
	rng uint32
	low uint32
	buff uint8
	cnt int
	count []uint16
	count_sum []uint32
	count_all float64
}

func (p *Encoder) init(file *os.File){
	p.file = file
	p.rng = MAX_RANGE
}

func (p *Encoder) init_count_table(count []uint32){
	var max uint32
	var maxi int
	for i, x := range count {
		if x > max {
			max = x
		}
		if x > 0 {
			maxi = i
		}
	}
	fmt.Println(max, maxi)
	counts := count[:maxi + 1]

	p.count = make([]uint16, len(counts))

	// create uint16 count table
	if max > 0xffff {
		var n uint
		m := max
		for m > 0xffff {
			m >>= 1
			n += 1
		}

		for i, x := range counts {
			if x != 0 {
				p.count[i] = uint16((x >> n) | 1)
			}
		}

	}else{
		for i, x := range counts {
			p.count[i] = uint16(x)
		}
	}

	// sum count
	p.count_sum = make([]uint32, len(counts) + 1)
	for i, x := range p.count {
		p.count_sum[i + 1] = p.count_sum[i] + uint32(x)
	}
	p.count_all = float64(p.count_sum[len(p.count_sum) - 1])

	if p.count_sum[len(p.count_sum) - 1] > MIN_RANGE {
		fmt.Println("count_all > MIN_RANGE")
	}
}

func (p *Encoder) write_count_table(){
	binary.Write(p.file, binary.LittleEndian, uint16(len(p.count)))
	binary.Write(p.file, binary.LittleEndian, p.count)
}

func (p *Encoder) encode(c uint16){
	temp := float64(p.rng) / p.count_all
	p.low += uint32(float64(p.count_sum[c]) * temp)
	p.rng = uint32(float64(p.count[c]) * temp)
	//if p.rng == 0 {
	//	fmt.Println("zero", p.rng, p.count[c], float64(p.count[c]) * temp)
	//}
	p.normalize()
}
func (p *Encoder) normalize(){
	// carry low
	if p.low >= MAX_RANGE {
		p.buff += 1
		p.low &= MASK

		if p.cnt > 0 {
			p.puti(p.buff)
			for i := 0; i < p.cnt - 1; i++ {
				p.puti(0)
			}
			p.buff = 0
			p.cnt = 0
		}
	}

	// scale range
	for p.rng < MIN_RANGE {
		if p.low < (0xff << SHIFT) {
			p.puti(p.buff)
			for i := 0; i < p.cnt; i++ {
				p.puti(0xff)
			}
			p.buff = uint8(p.low >> SHIFT)
			p.cnt = 0
		}else{
			p.cnt += 1
		}

		p.low = (p.low << 8) & MASK
		p.rng <<= 8
	}
}

func (p *Encoder) finish(){
	var c uint8 = 0xff
	if p.low >= MAX_RANGE {
		p.buff += 1
		c = 0
	}
	p.puti(p.buff)
	for i := 0; i < p.cnt; i++ {
		p.puti(c)
	}

	fmt.Println(p.low)
	binary.Write(p.file, binary.LittleEndian, p.low)
}

func (p *Encoder) puti(i uint8){
	binary.Write(p.file, binary.LittleEndian, i)
}

func readBinary(filename string) (size int64, array []uint16){
	fileinfo, _ := os.Stat(filename)
	size = fileinfo.Size()

	file, _ := os.Open(filename)
	defer file.Close()
	array = make([]uint16, size / 2)
	binary.Read(file, binary.LittleEndian, &array)
	return
}


//---------------------------------------------------------
// decode
//---------------------------------------------------------
func decode_file(input, output string){
	out, _ := os.Create(output)
	defer out.Close()

	decode(out, input)
}

func read_encoded(filename string) (int64, []uint8, []uint16){
	fileinfo, _ := os.Stat(filename)
	filesize := fileinfo.Size()

	file, _ := os.Open(filename)

	var size int64
	binary.Read(file, binary.LittleEndian, &size)

	count_table := read_count_table(file)

	datasize := int(filesize) - 8 - 2 * (len(count_table) + 1)
	fmt.Println(datasize)
	data := make([]uint8, datasize)
	err := binary.Read(file, binary.LittleEndian, &data)
	if err != nil {
		fmt.Println("binary.Read failed:", err)
	}

	return size, data, count_table
}

func read_count_table(file *os.File) (count_table []uint16){
	var maxi uint16
	binary.Read(file, binary.LittleEndian, &maxi)

	count_table = make([]uint16, maxi)
	binary.Read(file, binary.LittleEndian, &count_table)
	return
}

func decode(out *os.File, input string){
	size, data, count_table := read_encoded(input)

	decoder := &Decoder{}
	decoder.init(data)
	decoder.init_count_table(count_table)

	fmt.Println(size)
	for i := 0; i < int(size); i++ {
		code := decoder.decode()
		binary.Write(out, binary.LittleEndian, code)
	}
}

type Decoder struct {
	data []uint8
	readi int
	rng uint32
	low uint32
	count []uint16
	count_sum []uint32
	count_all float64
}

func (p *Decoder) init(data []uint8){
	p.data = data
	p.rng = MAX_RANGE

	p.low = (((((uint32(data[1]) << 8) + uint32(data[2])) << 8) + uint32(data[3])) << 8) + uint32(data[4])
	p.readi = 4
}

func (p *Decoder) init_count_table(count []uint16){
	p.count = count

	// sum count
	p.count_sum = make([]uint32, len(count) + 1)
	for i, x := range p.count {
		p.count_sum[i + 1] = p.count_sum[i] + uint32(x)
	}
	p.count_all = float64(p.count_sum[len(p.count_sum) - 1])
}

func (p *Decoder) decode() uint16 {
	temp := float64(p.rng)  / p.count_all
	code := p.search_code(uint32(float64(p.low) / temp))
	p.low -= uint32(temp * float64(p.count_sum[code]))
	p.rng = uint32(temp * float64(p.count[code]))
	p.normalize()

	return uint16(code)
}

func (p *Decoder) search_code(value uint32) int {
	i := 0
	j := len(p.count) - 1
	for i < j {
		med := int((i + j) / 2)
		if p.count_sum[med + 1] <= value {
			i = med + 1
		}else{
			j = med
		}
	}
	return i
}

func (p *Decoder) normalize() {
	for p.rng < MIN_RANGE {
		p.rng <<= 8
		p.readi += 1
		if p.readi >= len(p.data) {
			p.low = ((p.low << 8) + 0) & MASK
			return

		}else{
			c := p.data[p.readi]
			p.low = ((p.low << 8) + uint32(c)) & MASK
		}
	}
}

