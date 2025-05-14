import './Button.css';

export default function Button({
  children,
  active = true,
  type = 'primary',
  size = 'large',
  blackText = false,
  buttonType = "button",
  shine = false,
  ...attributes
}) {
  return (
    <button
      className={`button ${type} ${size} ${blackText ? 'black-text' : ''} ${shine ? 'shine' : ''}`}
      disabled={!active}
      type={buttonType}
      {...attributes}
    >
      {active ? '' : <div className='inactive'></div>}

      {type.indexOf('primary') != -1? 
        <div className='backPrimary'/>
      :
        <div className='backSecondary'/>
      }

      <div className='gradientBorder'/>
      {children}
    </button>
  );
}