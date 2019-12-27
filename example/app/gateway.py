from metropolis import Gateway
import settings


gateway = Gateway(__name__, settings)
gateway.app.run(host='0.0.0.0')
