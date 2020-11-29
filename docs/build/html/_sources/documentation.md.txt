# 📚 Documentation

## 📔 Source Jumbo Documentation

```{toctree}
   :maxdepth: 4

   Modules <modules.rst>
```

## 📃 Logging
Jumbo implements logging for many of its functions via the Python standard
 library `logging` package. The loggers which have been implemented are
  named as follows:
  
  - `jumbo`
  - `jumbo.config`
  - `jumbo.database`
  - `jumbo.handlers`
  - `jumbo.utils`

If your using application does not use logging, then only events of severity
 `WARNING` and greater will be printed to `sys.stderr`, thanks to the
  logger's last resort handler. This is regarded as the best default behaviour.

````{note}
It is strongly recommended to use logging in your applications. The following
code snippet will set you up with a basic logger:

   ```python
   import logging
    
   # Setup your basic logger
   logging.basicConfig(
       format='[%(asctime)s] %(levelname)s | %(message)s',
       datefmt='%D %H:%M:%S'
   )
    
   logger = logging.getLogger(__name__)  
   logger.setLevel("INFO")
   
   logger.info("Amazing!")
   ```

````

````{tip}
It is quite useful to lower the severity level for which jumbo logs
 are emitted. It is then easier to track which transactions are being
 executed by jumbo behind the scenes. Just add the following line after
 having configured your own logger:

   ```python
   # lower the severity level of jumbo logs being displayed
   logging.getLogger('jumbo').setLevel("INFO")
   ```

````