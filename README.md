# interpret
Interpret English into Hobbsian logical forms

Build and run the image:
```
; ./build
; ./run
```

Send requests:
```
; ./client Jack ate dinner.
```
or
```
; curl -d '{"s": "Jack ate dinner."}' http://localhost:5000/parse
```
