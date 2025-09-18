import java.util.List;
import java.util.ArrayList;
import java.util.Iterator;

/** Documents are the unit of indexing and search.
 *
 * A Document is a set of fields.  Each field has a name and a textual value.
 * A field may be {@link Fieldable#isStored() stored} with the document, in which
 * case it is returned with search hits on the document.  Thus each document
 * should typically contain one or more stored fields which uniquely identify
 * it.
 */

public final class Document {
  
  public interface Fieldable {
    String name();  
    String stringValue();
    boolean  isBinary();
    byte[] getBinaryValue();
  }

  List<Fieldable> fields = new ArrayList<Fieldable>();
  private float boost = 1.0f;

  /** Constructs a new document with no fields. */
  public Document() {}

  public void setBoost(float boost) {
    this.boost = boost;
  }

  public float getBoost() {
    return boost;
  }

  /**
   * <p>Adds a field to a document.  Several fields may be added with
   * the same name.  In this case, if the fields are indexed, their text is
   * treated as though appended for the purposes of search.</p>
   */
  public final void add(Fieldable field) {
    fields.add(field);
  }
  
  /**
   * <p>Removes field with the specified name from the document.
   * If multiple fields exist with this name, this method removes the first field that has been added.
   * If there is no field with the specified name, the document remains unchanged.</p>
   */
  public final void removeField(String name) {
    Iterator<Fieldable> it = fields.iterator();
    while (it.hasNext()) {
      Fieldable field = it.next();
      if (field.name().equals(name)) {
        it.remove();
        return;
      }
    }
  }
  
  /**
   * <p>Removes all fields with the given name from the document.
   * If there is no field with the specified name, the document remains unchanged.</p>
   */
  public final void removeFields(String name) {
    Iterator<Fieldable> it = fields.iterator();
    while (it.hasNext()) {
      Fieldable field = it.next();
      if (field.name().equals(name)) {
        it.remove();
      }
    }
  }

 /** Returns a field with the given name if any exist in this document, or
   * null.  If multiple fields exists with this name, this method returns the
   * first value added.
   */
 public Fieldable getFieldable(String name) {
   for (Fieldable field : fields) {
     if (field.name().equals(name))
       return field;
   }
   return null;
 }

  /** Returns the string value of the field with the given name if any exist in
   * this document, or null.  If multiple fields exist with this name, this
   * method returns the first value added. If only binary fields with this name
   * exist, returns null.
   */
  public final String get(String name) {
   for (Fieldable field : fields) {
      if (field.name().equals(name) && (!field.isBinary()))
        return field.stringValue();
    }
    return null;
  }

  /** Returns a List of all the fields in a document.
   */
  public final List<Fieldable> getFields() {
    return fields;
  }

   private final static Fieldable[] NO_FIELDABLES = new Fieldable[0];

   /**
   * Returns an array of {@link Fieldable}s with the given name.
   * This method returns an empty array when there are no
   * matching fields.  It never returns null.
   */
   public Fieldable[] getFieldables(String name) {
     List<Fieldable> result = new ArrayList<Fieldable>();
     for (Fieldable field : fields) {
       if (field.name().equals(name)) {
         result.add(field);
       }
     }

     if (result.size() == 0)
       return NO_FIELDABLES;

     return result.toArray(new Fieldable[result.size()]);
   }


   private final static String[] NO_STRINGS = new String[0];

  /**
   * Returns an array of values of the field specified as the method parameter.
   * This method returns an empty array when there are no
   * matching fields.  It never returns null.
   */
  public final String[] getValues(String name) {
    List<String> result = new ArrayList<String>();
    for (Fieldable field : fields) {
      if (field.name().equals(name) && (!field.isBinary()))
        result.add(field.stringValue());
    }
    
    if (result.size() == 0)
      return NO_STRINGS;
    
    return result.toArray(new String[result.size()]);
  }

  private final static byte[][] NO_BYTES = new byte[0][];

  /**
  * Returns an array of byte arrays for of the fields that have the name specified
  * as the method parameter.  This method returns an empty
  * array when there are no matching fields.  It never
  * returns null.
  */
  public final byte[][] getBinaryValues(String name) {
    List<byte[]> result = new ArrayList<byte[]>();
    for (Fieldable field : fields) {
      if (field.name().equals(name) && (field.isBinary()))
        result.add(field.getBinaryValue());
    }
  
    if (result.size() == 0)
      return NO_BYTES;
  
    return result.toArray(new byte[result.size()][]);
  }
  
  /**
  * Returns an array of bytes for the first (or only) field that has the name
  * specified as the method parameter. This method will return <code>null</code>
  * if no binary fields with the specified name are available.
  * There may be non-binary fields with the same name.
  */
  public final byte[] getBinaryValue(String name) {
    for (Fieldable field : fields) {
      if (field.name().equals(name) && (field.isBinary()))
        return field.getBinaryValue();
    }
    return null;
  }
  
  /** Prints the fields of a document for human consumption. */
  @Override
  public final String toString() {
    StringBuilder buffer = new StringBuilder();
    buffer.append("Document<");
    for (int i = 0; i < fields.size(); i++) {
      Fieldable field = fields.get(i);
      buffer.append(field.toString());
      if (i != fields.size()-1)
        buffer.append(" ");
    }
    buffer.append(">");
    return buffer.toString();
  }
}