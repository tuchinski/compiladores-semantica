all:
	clang -emit-llvm -S io.c
	llc -march=x86-64 -filetype=obj io.ll -o io.o
	python geracao.py
	llvm-link teste.ll io.ll -o meu_modulo.bc
	clang meu_modulo.bc -o meu_modulo.o
	#./meu_modulo.o

clean:
	rm *.ll *.o *.bc