import PropTypes from "prop-types";
import styles from "./title.module.css";

const Title = ({children, size=28, weight=500}) => {
  return (
    <div className={styles.PageTitle} style={{
        'font-size': `${size}px`,
        'font-weight': `${weight}`,
      }}
    >
      {children}
    </div>
  );
};

Title.propTypes = {
  children: PropTypes.element.isRequired
};

export default Title;
