# control-panel

## Project setup
```
npm install
```

### Compiles and hot-reloads for development
```
npm run serve
```

### Compiles and minifies for production
```
npm run build
```

### Lints and fixes files
```
npm run lint
```

### Mock server for localhost
```
npx json-server --watch mocks/data.json --routes mocks/routes.json --port 5000 --middlewares mocks/cors.js
```

- Public API URL: http://localhost:8080/api
- Private API URL: http://localhost:8080/api
- Event ID: 1

Otherwise enter a dummy value.

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).
