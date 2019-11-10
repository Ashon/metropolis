from metropolis import Gateway
import settings


gateway = Gateway(settings)
gateway.app.run(host='0.0.0.0')
