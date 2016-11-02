# interpret
Interpret English into Hobbsian logical forms

Build and run the image:
```
; ./build
; ./run
```

Send requests:
```
; ./client I interrogated him.
```
or
```
; curl -d '{"s": "I interrogated him."}' http://localhost:5000/parse
```
