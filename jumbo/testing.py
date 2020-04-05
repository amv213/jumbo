# Make sure this is pointing to local development version of the package - and not pip.
# (i.e. uninstall jumbo and add path to sys.path if not already done)
import jumbo

if __name__ == "__main__":

    # Use custom config file for testing purposes
    config = jumbo.config.Config(env_path="T:\\DATA\\Lattice Clock\\!Strontium OLC\\python\\Alvise Python Scripts")

    database = jumbo.database.Database(config)

    with database.open() as pool:
        
        with pool.connect(key=1):

            pass
